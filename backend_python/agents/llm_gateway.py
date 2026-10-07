import os
import re
import json
import time
import logging
import asyncio
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, ValidationError

from dotenv import load_dotenv

# Provider SDKs
from google import genai
from google.genai import types
from groq import Groq

load_dotenv()

log = logging.getLogger("llm_gateway")
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] [%(asctime)s] %(name)s: %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)


# ═══════════════════════════════════════════════════════════════
# ERROR DEFINITIONS & USER-SAFE MESSAGES
# ═══════════════════════════════════════════════════════════════

USER_SAFE_MESSAGES = {
    "RATE_LIMITED": "AI busy. Try again shortly.",
    "ALL_EXHAUSTED": "Service busy. Please retry later.",
    "SCHEMA_MISMATCH": "Formatting error. Please re-try.",
    "BAD_REQUEST": "Invalid input. Please check resume.",
    "TIMEOUT": "Request timed out. Please retry.",
    "AUTH_FAILED": "Service configuration error.",
    "UNEXPECTED": "Something went wrong. Please retry.",
}


class GatewayError(Exception):
    """Unified error carrying server details and a toast-safe user message."""

    def __init__(self, code: str, raw_message: str, user_message: Optional[str] = None):
        self.code = code
        self.raw_message = raw_message
        self.user_message = user_message or USER_SAFE_MESSAGES.get(code, USER_SAFE_MESSAGES["UNEXPECTED"])
        super().__init__(f"[{self.code}] {self.raw_message}")


# ═══════════════════════════════════════════════════════════════
# ROBUST JSON PARSER & CLEANER
# ═══════════════════════════════════════════════════════════════

def extract_and_parse_json(raw_text: str, schema: Optional[Type[BaseModel]] = None) -> Any:
    """Strips markdown fences, locates outermost JSON brackets, and validates against Pydantic schema."""
    cleaned = raw_text.strip()

    # 1. Strip markdown fences (```json ... ``` or ``` ...)
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # 2. Parse JSON
    parsed: Any
    try:
        parsed = json.loads(cleaned)
    except Exception:
        # Fallback: Find outermost { ... } or [ ... ]
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        first_bracket = cleaned.find("[")
        last_bracket = cleaned.rfind("]")

        start = -1
        end = -1
        if first_brace != -1 and last_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            start = first_brace
            end = last_brace + 1
        elif first_bracket != -1 and last_bracket != -1:
            start = first_bracket
            end = last_bracket + 1

        if start != -1 and end != -1 and end > start:
            parsed = json.loads(cleaned[start:end])
        else:
            raise GatewayError(
                code="SCHEMA_MISMATCH",
                raw_message=f"No valid JSON structure found in text: {raw_text[:200]}...",
            )

    # 3. Unwrap common outer wrappers produced by models (e.g. { "response": { ... } })
    if isinstance(parsed, dict):
        for wrapper_key in ("response", "data", "result", "payload"):
            if wrapper_key in parsed and isinstance(parsed[wrapper_key], (dict, list)) and len(parsed) == 1:
                parsed = parsed[wrapper_key]
                break

    # 4. Optional Pydantic Validation
    if schema:
        try:
            if hasattr(schema, "model_validate"):
                return schema.model_validate(parsed)
            elif hasattr(schema, "parse_obj"):
                return schema.parse_obj(parsed)
        except ValidationError as val_err:
            raise GatewayError(
                code="SCHEMA_MISMATCH",
                raw_message=f"Pydantic schema validation failed: {str(val_err)}",
            )

    return parsed


# ═══════════════════════════════════════════════════════════════
# LLM GATEWAY CLASS
# ═══════════════════════════════════════════════════════════════

class LLMGateway:
    """Production Multi-Key & Multi-Model Gateway for Gemini and Groq."""

    def __init__(self):
        # 1. Load & Deduplicate Gemini API Keys Pool
        self.gemini_keys: List[str] = self._load_gemini_keys()
        self.gemini_key_index: int = 0
        self.key_cooldowns: Dict[str, float] = {}

        # 2. Load Groq Key
        self.groq_api_key: str = os.getenv("GROQ_API", "").strip()
        self.groq_client: Optional[Groq] = Groq(api_key=self.groq_api_key) if self.groq_api_key else None

        # 3. Model Cascades per Workload
        self.cascades: Dict[str, List[str]] = {
            "tailor": self._load_model_list(
                "GEMINI_TAILOR_MODELS",
                [
                    "gemini-3.8-flash",
                    "gemini-3.7-flash",
                    "gemini-3.6-flash",
                    "gemini-3.5-flash",
                    "gemini-3-flash",
                    "gemini-2.5-flash",
                    "gemini-3.5-flash-lite",
                ],
            ),
            "parse": self._load_model_list(
                "GEMINI_PARSE_MODELS",
                [
                    "gemini-3.5-flash-lite",
                    "gemini-3.1-flash-lite",
                    "gemini-2.5-flash",
                    "gemini-2.5-flash-lite",
                ],
            ),
            "scraper": self._load_model_list(
                "GEMINI_SCRAPER_MODELS",
                [
                    "gemini-3.5-flash-lite",
                    "gemini-3.1-flash-lite",
                    "gemini-3.8-flash",
                    "gemini-2.5-flash",
                ],
            ),
            "scout": [os.getenv("GROQ_SCOUT_MODEL", "qwen/qwen3.8-27b").strip()],
            "single_tailor": [os.getenv("GROQ_TAILOR_MODEL", "openai/gpt-oss-120b").strip()],
            "default": [
                "gemini-3.5-flash-lite",
                "gemini-3.1-flash-lite",
                "gemini-2.5-flash",
            ],
        }

        log.info(
            "[LLM Gateway] Initialized with %d Gemini Key(s), Groq: %s",
            len(self.gemini_keys),
            "Enabled" if self.groq_client else "Disabled",
        )

    # ── Key Pool Management ────────────────────────────────────

    def _load_gemini_keys(self) -> List[str]:
        raw_multi = os.getenv("GEMINI_API_KEYS", "")
        raw_single = os.getenv("GOOGLE_API", "")

        keys: List[str] = []
        if raw_multi:
            for k in raw_multi.split(","):
                k_clean = k.strip()
                if k_clean and k_clean not in keys:
                    keys.append(k_clean)

        if raw_single:
            k_single = raw_single.strip()
            if k_single and k_single not in keys:
                keys.append(k_single)

        return keys

    def _load_model_list(self, env_var: str, default: List[str]) -> List[str]:
        raw = os.getenv(env_var, "")
        if raw.strip():
            custom = [m.strip() for m in raw.split(",") if m.strip()]
            if custom:
                return custom
        return default

    def mark_key_cooldown(self, key: str, cooldown_secs: float = 60.0):
        """Mark a key as cooling down until epoch timestamp."""
        self.key_cooldowns[key] = time.time() + cooldown_secs

    def is_key_cooling(self, key: str) -> bool:
        """Check if key is in active cooldown."""
        expires_at = self.key_cooldowns.get(key)
        if not expires_at:
            return False
        if time.time() > expires_at:
            self.key_cooldowns.pop(key, None)
            return False
        return True

    def get_next_gemini_key(self) -> str:
        """Round-robin through non-cooling keys; fall back to earliest expiring key."""
        if not self.gemini_keys:
            raise GatewayError("AUTH_FAILED", "No Gemini API keys configured in environment.")

        # 1. Filter active keys not in cooldown
        active_keys = [k for k in self.gemini_keys if not self.is_key_cooling(k)]
        if active_keys:
            key = active_keys[self.gemini_key_index % len(active_keys)]
            self.gemini_key_index += 1
            return key

        # 2. If all keys are in cooldown, pick the one expiring earliest
        earliest_key = min(self.gemini_keys, key=lambda k: self.key_cooldowns.get(k, 0))
        return earliest_key

    # ── Error Classifier ───────────────────────────────────────

    def classify_error(self, err: Exception, provider: str = "gemini") -> Dict[str, Any]:
        raw_msg = str(err)
        status_code = getattr(err, "code", getattr(err, "status_code", 0))

        # Check for status code inside string if missing
        if not status_code:
            status_match = re.search(r"\b(4\d\d|5\d\d)\b", raw_msg)
            if status_match:
                status_code = int(status_match.group(1))

        code = "UNEXPECTED"
        retryable = False

        if status_code == 429 or "RESOURCE_EXHAUSTED" in raw_msg or "rate limit" in raw_msg.lower():
            code = "RATE_LIMITED"
            retryable = True
        elif status_code in (408, 504) or "timeout" in raw_msg.lower() or "timed out" in raw_msg.lower():
            code = "TIMEOUT"
            retryable = False  # Switch model immediately rather than waiting on hanging endpoint
        elif status_code in (401, 403) or "api_key" in raw_msg.lower() or "invalid api key" in raw_msg.lower():
            code = "AUTH_FAILED"
            retryable = False
        elif status_code in (404, 410) or "not found" in raw_msg.lower() or "model_gone" in raw_msg.lower():
            code = "MODEL_GONE"
            retryable = False  # Model doesn't exist or deprecated -> cascade to next model
        elif status_code in (500, 502, 503, 529) or "overloaded" in raw_msg.lower():
            code = "OVERLOADED"
            retryable = True
        elif status_code == 400:
            code = "BAD_REQUEST"
            retryable = False  # Client syntax error -> fatal, do not waste retries

        return {
            "code": code,
            "status_code": status_code,
            "retryable": retryable,
            "raw_message": raw_msg,
            "user_message": USER_SAFE_MESSAGES.get(code, USER_SAFE_MESSAGES["UNEXPECTED"]),
        }

    # ── Execution: Groq Provider ───────────────────────────────

    def _call_groq(
        self,
        prompt: str,
        model: str,
        schema: Optional[Type[BaseModel]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> Any:
        if not self.groq_client:
            raise GatewayError("AUTH_FAILED", "Groq client requested but GROQ_API key is not configured.")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        request_kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_output_tokens:
            request_kwargs["max_tokens"] = max_output_tokens

        if schema:
            request_kwargs["response_format"] = {"type": "json_object"}

        try:
            log.info("[LLM Gateway] [Groq] Trying model: %s", model)
            response = self.groq_client.chat.completions.create(**request_kwargs)
            content = response.choices[0].message.content or ""
            if not content.strip():
                raise GatewayError("SCHEMA_MISMATCH", "Empty content returned from Groq.")

            if schema:
                return extract_and_parse_json(content, schema=schema)
            return content
        except GatewayError:
            raise
        except Exception as e:
            classified = self.classify_error(e, provider="groq")
            log.warning("[LLM Gateway] [Groq] Model %s failed: [%s] %s", model, classified["code"], classified["raw_message"][:150])
            raise GatewayError(classified["code"], classified["raw_message"], classified["user_message"])

    # ── Execution: Gemini Multi-Key Provider ───────────────────

    def _call_gemini(
        self,
        contents: Any,
        task: str,
        schema: Optional[Type[BaseModel]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> Any:
        models_to_try = self.cascades.get(task, self.cascades["default"])
        max_key_attempts = max(len(self.gemini_keys), 1)
        last_error_info: Optional[Dict[str, Any]] = None

        # Model-Outer -> Key-Inner loop (Preserves maximum output quality)
        for model in models_to_try:
            log.info("[LLM Gateway] [Gemini] Task '%s' -> Trying model: %s", task, model)

            for key_attempt in range(max_key_attempts):
                api_key = self.get_next_gemini_key()
                key_preview = f"...{api_key[-4:]}" if len(api_key) > 4 else "key"

                try:
                    client = genai.Client(api_key=api_key)

                    config_kwargs: Dict[str, Any] = {
                        "temperature": temperature,
                    }
                    if system_instruction:
                        config_kwargs["system_instruction"] = system_instruction
                    if max_output_tokens:
                        config_kwargs["max_output_tokens"] = max_output_tokens

                    if schema:
                        config_kwargs["response_mime_type"] = "application/json"
                        config_kwargs["response_schema"] = schema

                    config = types.GenerateContentConfig(**config_kwargs)

                    response = client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config,
                    )

                    # Return parsed Pydantic model if populated by SDK
                    if schema and hasattr(response, "parsed") and response.parsed is not None:
                        log.info("[LLM Gateway] [Gemini] Success on model: %s (Key %s)", model, key_preview)
                        return response.parsed

                    raw_text = response.text or ""
                    if not raw_text.strip():
                        raise GatewayError("SCHEMA_MISMATCH", "Empty response from Gemini model.")

                    if schema:
                        parsed = extract_and_parse_json(raw_text, schema=schema)
                        log.info("[LLM Gateway] [Gemini] Success on model: %s (Key %s)", model, key_preview)
                        return parsed

                    log.info("[LLM Gateway] [Gemini] Success on model: %s (Key %s)", model, key_preview)
                    return raw_text

                except GatewayError:
                    raise
                except Exception as err:
                    classified = self.classify_error(err, provider="gemini")
                    last_error_info = classified

                    if classified["code"] == "RATE_LIMITED":
                        self.mark_key_cooldown(api_key, cooldown_secs=60.0)
                        log.warning(
                            "[LLM Gateway] Key %s rate limited on %s, cooling down for 60s. Rotating key...",
                            key_preview,
                            model,
                        )
                        continue  # Try next key on the same model

                    if classified["code"] == "AUTH_FAILED":
                        self.mark_key_cooldown(api_key, cooldown_secs=86400.0)
                        log.warning("[LLM Gateway] Key %s auth failed, quarantining for 24h. Rotating key...", key_preview)
                        continue

                    if classified["code"] in ("MODEL_GONE", "OVERLOADED"):
                        log.warning(
                            "[LLM Gateway] Model %s returned %s. Cascading to next model...",
                            model,
                            classified["code"],
                        )
                        break  # Break key loop, advance to next model

                    if classified["code"] == "BAD_REQUEST":
                        log.error("[LLM Gateway] Fatal Bad Request (400): %s", classified["raw_message"][:200])
                        raise GatewayError("BAD_REQUEST", classified["raw_message"])

                    # Other errors -> try next key or break
                    break

        user_msg = USER_SAFE_MESSAGES["ALL_EXHAUSTED"]
        raw_detail = last_error_info["raw_message"] if last_error_info else "All models and keys failed."
        log.error("[LLM Gateway] Exhausted all models & keys for task '%s': %s", task, raw_detail[:200])
        raise GatewayError("ALL_EXHAUSTED", raw_detail, user_msg)

    # ── Public API: Unified Generate ───────────────────────────

    def generate(
        self,
        contents: Any,
        task: str = "default",
        schema: Optional[Type[BaseModel]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
    ) -> Any:
        """Unified entry point for all agent LLM calls."""
        # 1. Single Tailoring: Opportunistic Groq -> Gemini Flash Failover
        if task == "single_tailor":
            if self.groq_client:
                groq_model = self.cascades["single_tailor"][0]
                try:
                    return self._call_groq(
                        prompt=str(contents),
                        model=groq_model,
                        schema=schema,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=max_output_tokens or 8192,
                    )
                except GatewayError as g_err:
                    log.warning("🔄 [LLM Gateway] Single-tailor Groq failed (%s), falling back to Gemini cascade...", g_err.code)

            # Fallback directly to high-capacity Gemini Flash cascade
            return self._call_gemini(
                contents=contents,
                task="tailor",
                schema=schema,
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_output_tokens or 65536,
            )

        # 2. Scout Mode: Form questions on Groq Qwen 27B -> Gemini Fallback
        if task == "scout":
            if self.groq_client:
                scout_model = self.cascades["scout"][0]
                try:
                    return self._call_groq(
                        prompt=str(contents),
                        model=scout_model,
                        schema=schema,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=max_output_tokens or 2048,
                    )
                except GatewayError as g_err:
                    log.warning("🔄 [LLM Gateway] Scout Groq failed (%s), falling back to Gemini Flash-Lite...", g_err.code)

            # Fallback to Gemini Flash-Lite
            return self._call_gemini(
                contents=contents,
                task="parse",
                schema=schema,
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )

        # 3. All Other Tasks (tailor, parse, scraper, default): 4-Key Gemini Gateway
        return self._call_gemini(
            contents=contents,
            task=task,
            schema=schema,
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

    async def generate_async(self, *args, **kwargs) -> Any:
        """Async-safe generation wrapper running in a thread pool."""
        return await asyncio.to_thread(self.generate, *args, **kwargs)


# ═══════════════════════════════════════════════════════════════
# GLOBAL SINGLETON EXPORT
# ═══════════════════════════════════════════════════════════════
gemini_gateway = LLMGateway()
