from config import GOOGLE_API, GROQ_API
import requests
import fitz
import io
import re
import json
import os
from .pdf_utils import extract_pdf_text_from_url
from google import genai
from google.genai import types
from pdf2image import convert_from_bytes
import pytesseract
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class LocationSchema(BaseModel):
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    full_location: Optional[str]

class UserContactSchema(BaseModel):
    first: Optional[str]
    last: Optional[str]
    email: Optional[str]
    phone: Optional[str]

class UserProfileSchema(BaseModel):
    titles: List[str]
    keywords: List[str]
    candidate_name: Optional[str]
    location: Optional[LocationSchema]
    user: Optional[UserContactSchema]
    general_experience_years: Optional[float]
    known_tech_experience_years: Optional[float]
    unknown_tech_experience_years: Optional[float]
    current_ctc: Optional[str]
    expected_ctc: Optional[str]
    notice_period: Optional[str]
    tech_stacks: List[str]
    tools: List[str]
    sure_skills: List[str]
    additional_skills: List[str]


class TitleCandidatesSchema(BaseModel):
    titles: List[str]


client  = genai.Client(api_key= GOOGLE_API)
model = 'gemini-2.5-flash-lite'
# client = Groq(
#     api_key=GROQ_API,
# )
# model="llama-3.3-70b-versatile"


TITLE_LIMIT = 5
SKILL_LIMIT = 40
ADDITIONAL_SKILL_LIMIT = 5
MAX_INFERRED_TITLES = 20
EXPERIENCE_DECIMALS = 1

PLACEHOLDER_TITLES = {
    "title",
    "job title",
    "software",
    "developer",
    "engineer",
    "not specified",
    "unknown",
    "n/a",
}

EARLY_CAREER_RESTRICTED_WORDS = {
    "senior",
    "lead",
    "principal",
    "architect",
    "head",
    "director",
    "manager",
}

ROLE_SUFFIXES = {
    "engineer",
    "developer",
    "analyst",
    "consultant",
    "administrator",
    "architect",
    "specialist",
    "scientist",
    "designer",
    "tester",
    "manager",
}

SKILL_STOPWORDS = {
    "project",
    "projects",
    "team",
    "teams",
    "client",
    "clients",
    "work",
    "worked",
    "experience",
    "responsible",
    "development",
    "application",
    "applications",
    "system",
    "systems",
    "technology",
    "technologies",
    "engineering",
    "software",
    "tool",
    "tools",
    "platform",
}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("_", " ").split())


def normalize_candidate_name(value: Any) -> Optional[str]:
    cleaned = normalize_text(value)
    if not cleaned:
        return None
    return "_".join(cleaned.split())


def normalize_list(values: Any, max_items: Optional[int] = None) -> List[str]:
    if not isinstance(values, list):
        return []

    seen = set()
    out: List[str] = []
    for item in values:
        cleaned = normalize_text(item)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
        if max_items is not None and len(out) >= max_items:
            break
    return out


def round_experience_years(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    if value < 0:
        return None
    return round(value, EXPERIENCE_DECIMALS)


def parse_experience_years(value: Any) -> Optional[float]:
    """Normalize experience input to decimal years (e.g., 0.3, 0.6, 1.5)."""
    if value is None:
        return None

    # Bool should not be treated as numeric years.
    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return round_experience_years(float(value))

    text = normalize_text(value).lower()
    if not text:
        return None

    # Range format: "6-8 months" or "1 to 2 years".
    range_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(years?|yrs?|months?|mos?)",
        text,
    )
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        unit = range_match.group(3)
        midpoint = (low + high) / 2.0
        if unit.startswith("month") or unit.startswith("mo"):
            return round_experience_years(midpoint / 12.0)
        return round_experience_years(midpoint)

    years_match = re.search(r"(\d+(?:\.\d+)?)\s*(years?|yrs?)", text)
    months_match = re.search(r"(\d+(?:\.\d+)?)\s*(months?|mos?)", text)
    if years_match or months_match:
        years = float(years_match.group(1)) if years_match else 0.0
        months = float(months_match.group(1)) if months_match else 0.0
        return round_experience_years(years + (months / 12.0))

    number_match = re.search(r"\d+(?:\.\d+)?", text)
    if number_match:
        return round_experience_years(float(number_match.group(0)))

    if re.search(r"\b(fresher|entry\s*level|intern)\b", text):
        return 0.0

    return None


def normalize_experience_fields(profile: Dict[str, Any]) -> None:
    general = parse_experience_years(profile.get("general_experience_years"))
    known = parse_experience_years(profile.get("known_tech_experience_years"))
    unknown = parse_experience_years(profile.get("unknown_tech_experience_years"))

    if general is not None and known is not None and known > general:
        known = general

    if unknown is None and general is not None and known is not None:
        unknown = round_experience_years(max(general - known, 0.0))

    if general is None and known is not None and unknown is not None:
        general = round_experience_years(known + unknown)

    profile["general_experience_years"] = general
    profile["known_tech_experience_years"] = known
    profile["unknown_tech_experience_years"] = unknown


def normalize_title(title: Any) -> str:
    cleaned = normalize_text(title)
    cleaned = re.sub(r"\s*[-|]+\s*", " ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" ,.-")
    cleaned = cleaned.title()
    return cleaned


def title_looks_valid(title: str) -> bool:
    lower = title.lower()
    if not lower or lower in PLACEHOLDER_TITLES:
        return False
    if len(title.split()) < 2:
        return False
    if len(title) > 80:
        return False
    return True


def collect_resume_role_candidates(resume_text: str) -> List[str]:
    if not resume_text:
        return []

    role_pattern = re.compile(
        r"\b([A-Za-z][A-Za-z&/,+\-\s]{2,70}"
        r"(?:Engineer|Developer|Analyst|Consultant|Administrator|Architect|"
        r"Specialist|Scientist|Designer|Tester|Intern|Manager))\b",
        re.IGNORECASE,
    )

    found = role_pattern.findall(resume_text)
    normalized = [normalize_title(role) for role in found]
    return normalize_list(normalized, max_items=20)


def extract_role_suffixes(titles: List[str]) -> List[str]:
    suffixes: List[str] = []
    for title in titles:
        parts = title.split()
        if not parts:
            continue
        suffix = parts[-1].lower()
        if suffix in ROLE_SUFFIXES:
            suffixes.append(parts[-1].title())

    return normalize_list(suffixes, max_items=6)


def extract_skill_qualifiers(profile: Dict[str, Any], resume_text: str) -> List[str]:
    raw_qualifiers: List[str] = []

    for field in ("sure_skills", "tech_stacks", "tools", "keywords", "additional_skills"):
        raw_qualifiers.extend(normalize_list(profile.get(field), max_items=SKILL_LIMIT))

    # Pick compact role-modifier phrases from resume text (e.g., "React", "Data", "Cloud").
    resume_phrase_pattern = re.compile(r"\b([A-Za-z][A-Za-z0-9.+#/\-]{1,20})\s+(?:Engineer|Developer|Analyst|Designer|Scientist)\b", re.IGNORECASE)
    raw_qualifiers.extend([normalize_text(m) for m in resume_phrase_pattern.findall(resume_text)])

    cleaned: List[str] = []
    for item in raw_qualifiers:
        value = normalize_text(item)
        if not value:
            continue

        key = value.lower()
        if key in SKILL_STOPWORDS:
            continue

        if len(value) < 2 or len(value) > 25:
            continue

        if value.isdigit():
            continue

        cleaned.append(value)

    return normalize_list(cleaned, max_items=20)


def infer_titles_from_resume_signals(
    profile: Dict[str, Any],
    resume_text: str,
    known_titles: List[str],
) -> List[str]:
    suffixes = extract_role_suffixes(known_titles)
    if not suffixes:
        suffixes = ["Developer", "Engineer"]

    qualifiers = extract_skill_qualifiers(profile, resume_text)
    inferred: List[str] = []

    for qualifier in qualifiers:
        for suffix in suffixes:
            title = normalize_title(f"{qualifier} {suffix}")
            if title_looks_valid(title):
                inferred.append(title)
            if len(inferred) >= MAX_INFERRED_TITLES:
                return normalize_list(inferred, max_items=MAX_INFERRED_TITLES)

    return normalize_list(inferred, max_items=MAX_INFERRED_TITLES)


def complete_titles_from_resume_with_llm(
    resume_text: str,
    profile: Dict[str, Any],
    existing_titles: List[str],
) -> List[str]:
    """Ask the model for missing title slots using only resume-backed evidence."""
    context_payload = {
        "existing_titles": normalize_list(existing_titles, max_items=TITLE_LIMIT),
        "keywords": normalize_list(profile.get("keywords"), max_items=20),
        "tech_stacks": normalize_list(profile.get("tech_stacks"), max_items=20),
        "tools": normalize_list(profile.get("tools"), max_items=20),
        "sure_skills": normalize_list(profile.get("sure_skills"), max_items=20),
        "general_experience_years": profile.get("general_experience_years"),
    }

    prompt = f"""
You are a strict resume role-matching expert.

TASK:
- Return exactly 5 distinct, resume-relevant job titles in ranked order.
- Prefer concrete roles the candidate can apply to immediately.
- Use only evidence from resume text and context JSON.
- Do not output vague placeholders (e.g., "Software", "Developer", "Engineer").
- Do not output aspirational senior titles unless clearly justified.

OUTPUT:
- JSON only with this schema: {{"titles": ["...", "...", "...", "...", "..."]}}

Context JSON:
{json.dumps(context_payload, ensure_ascii=False)}

Resume text:
{resume_text[:14000]}
"""

    try:
        raw = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.05,
                response_mime_type="application/json",
                response_schema=TitleCandidatesSchema,
            ),
        ).text

        if not raw:
            return []

        parsed = json.loads(raw)
        candidates = parsed.get("titles", []) if isinstance(parsed, dict) else []
        normalized = [normalize_title(t) for t in candidates]
        return [t for t in normalize_list(normalized, max_items=TITLE_LIMIT) if title_looks_valid(t)]
    except Exception:
        return []


def filter_titles_by_experience(titles: List[str], experience_years: Optional[float]) -> List[str]:
    if experience_years is None or experience_years >= 4:
        return titles

    filtered = []
    for title in titles:
        lower = title.lower()
        if any(word in lower for word in EARLY_CAREER_RESTRICTED_WORDS):
            continue
        filtered.append(title)
    return filtered


def normalize_profile(parsed_json: Dict[str, Any], resume_text: str) -> Dict[str, Any]:
    profile = dict(parsed_json or {})

    # Normalize scalar/user fields.
    profile["candidate_name"] = normalize_candidate_name(profile.get("candidate_name"))

    # Normalize skill lists.
    profile["keywords"] = normalize_list(profile.get("keywords"), max_items=SKILL_LIMIT)
    profile["tech_stacks"] = normalize_list(profile.get("tech_stacks"), max_items=SKILL_LIMIT)
    profile["tools"] = normalize_list(profile.get("tools"), max_items=SKILL_LIMIT)
    profile["sure_skills"] = normalize_list(profile.get("sure_skills"), max_items=SKILL_LIMIT)
    profile["additional_skills"] = normalize_list(
        profile.get("additional_skills"),
        max_items=ADDITIONAL_SKILL_LIMIT,
    )

    normalize_experience_fields(profile)

    # Build title candidates from model output first.
    raw_titles_value = profile.get("titles")
    raw_titles = raw_titles_value if isinstance(raw_titles_value, list) else []
    model_titles = [normalize_title(t) for t in raw_titles]
    model_titles = [t for t in model_titles if title_looks_valid(t)]

    # Augment with role mining and generic inference based on resume evidence.
    resume_titles = collect_resume_role_candidates(resume_text)
    inferred_titles = infer_titles_from_resume_signals(
        profile,
        resume_text,
        known_titles=model_titles + resume_titles,
    )

    combined = normalize_list(model_titles + resume_titles + inferred_titles)

    experience_years = profile.get("general_experience_years")
    if isinstance(experience_years, int):
        experience_years = float(experience_years)
    if not isinstance(experience_years, float):
        experience_years = None

    combined = filter_titles_by_experience(combined, experience_years)

    # Fill missing slots with another strict, resume-only title pass from the model.
    if len(combined) < TITLE_LIMIT:
        llm_completed_titles = complete_titles_from_resume_with_llm(
            resume_text=resume_text,
            profile=profile,
            existing_titles=combined,
        )
        combined = normalize_list(combined + llm_completed_titles)

    # If filtering removed too many entries, reuse unfiltered evidence candidates (still resume-backed).
    if len(combined) < TITLE_LIMIT:
        combined = normalize_list(combined + model_titles + resume_titles + inferred_titles)

    # Final guard: keep only non-vague, evidence-derived titles and limit to top TITLE_LIMIT.
    combined = [title for title in combined if title_looks_valid(title)]

    profile["titles"] = combined[:TITLE_LIMIT]
    # print(profile)
    return profile

def parse_pdf(url : str):
    text = extract_pdf_text_from_url(url)
    if len(text) < 500 or text.count('') > (len(text) / 2):
        print(text)
        raise ValueError("invalid pdf")
    print("data fetched from resume")
    return text

system_instruction = """
You are a senior talent intelligence parser specialized in resume-to-role mapping.
Your job is to extract only what is strongly supported by resume evidence.

OUTPUT CONTRACT:
- Return JSON only and strictly follow the provided schema.
- Use null for unknown string/number fields and [] for unknown list fields.
- Never hallucinate tools, skills, roles, years, CTC, or notice period.
- `general_experience_years`, `known_tech_experience_years`, and `unknown_tech_experience_years` MUST be numeric decimal years, never boolean.
- For partial experience, use decimal years (examples: 4 months -> 0.3, 7 months -> 0.6, 1 year 6 months -> 1.5).

TITLE QUALITY BAR (MOST IMPORTANT):
- `titles` must contain exactly 5 distinct, market-realistic, immediately-applicable job titles.
- Rank titles from most relevant to least relevant based on resume evidence.
- Prefer titles proven by RECENT experience + core skills + project stack.
- Titles must be role names, not skills. Good: "Backend Developer". Bad: "Python".
- Do not output vague placeholders such as only "Software", "Developer", or "Engineer".
- Do not output broad defaults unless clearly supported by resume evidence.
- Avoid aspirational titles not supported by evidence.
- If experience is low, avoid leadership-heavy titles (Lead, Principal, Architect, Head, Director, Manager).

PROFILE EXTRACTION RULES:
- `sure_skills`: include only skills explicitly present in resume text.
- `additional_skills`: include at most 5 skills weakly implied by context; do not copy all skills here.
- `keywords`, `tech_stacks`, and `tools` should be deduplicated, concise, and evidence-backed.
- `candidate_name` must use underscores instead of spaces.
- Experience fields represent years only (float), not categorical flags.

ANALYSIS PROCESS (perform internally, do not output these steps):
1) Identify core domain(s): backend/frontend/full-stack/data/ml/devops/mobile/qa/design/etc.
2) Identify strongest technologies and years/seniority clues.
3) Infer best-fit role family and rank top 5 role titles.
4) Populate remaining schema fields conservatively.
"""
              
def main(url):
    response: Any
    if url:
            resume_text = (parse_pdf(url))
            contents = f"Resume Content for Analysis:\n{resume_text}"                       
            
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.05,
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=UserProfileSchema
                )
            ).text
            
            try:
                parsed_json = json.loads(response)
            except Exception as e:
                # Fallback if markdown blocking occurs
                clean = response.replace('```json', '').replace('```', '').strip()
                parsed_json = json.loads(clean)

            return normalize_profile(parsed_json, resume_text)

        # inserting data into tables
            # if resumeNotExist(resume_id):
            #     newTitles = ParsedTitle(
            #         id=uuid.uuid4(),
            #         resume_id=resume_id,
            #         titles= titles
            #     )
            #     session.add(newTitles)
            #     session.commit()
            #     print("data inserted in parsed table")
            # else:
            #     print("titles already exists")
if __name__ == "__main__":
    main("https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/1772979043008_SRINIVAS_SAI_SARAN_TEJA%20(1).pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS8xNzcyOTc5MDQzMDA4X1NSSU5JVkFTX1NBSV9TQVJBTl9URUpBICgxKS5wZGYiLCJpYXQiOjE3NzI5NzkwNDUsImV4cCI6MTc4MTYxOTA0NX0.MC0oVvgYJoFj7ZU8_Hh1tlok73H8_GQDeM6Wwd7LO8E")