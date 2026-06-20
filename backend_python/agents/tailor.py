#!/usr/bin/env python3
"""
Batch résumé-tailoring pipeline – COLORED-DEBUG v3
──────────────────────────────────────────────────
-  Colour-coded logs.
-  Single download of the original PDF.
-  Robust prompt → Gemini now returns real LaTeX.
-  Tolerant parsing + graceful fallback.
"""

import base64
import json
import logging
import os
import random
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz
import requests                       # PyMuPDF / HTTP
from google import genai
from google.genai import types
from config import GOOGLE_API
from pydantic import BaseModel, Field, ConfigDict
from jinja2 import Environment, FileSystemLoader

# ╭─────────────────────────  COLOUR LOG  ─────────────────────────╮
class _C:
    R = "\33[31m"
    G = "\33[32m"
    Y = "\33[33m"
    C = "\33[36m"
    M = "\33[35m"
    Z = "\33[0m"
_PALETTE = {"DEBUG": _C.C, "INFO": _C.G, "WARNING": _C.Y, "ERROR": _C.R, "CRITICAL": _C.M}
class _Fmt(logging.Formatter):
    def format(self, rec):
        rec.levelname = f"{_PALETTE.get(rec.levelname, _C.Z)}{rec.levelname}{_C.Z}"
        return super().format(rec)
hlr = logging.StreamHandler()
hlr.setFormatter(_Fmt("%(asctime)s | %(levelname)s | %(message)s"))
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), handlers=[hlr])
log = logging.getLogger("tailor")
_TEMPLATE = 0
# ╰───────────────────────────────────────────────────────────────╯

jinja_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent)), # Use current script's directory
    block_start_string='<BLOCK>',
    block_end_string='</BLOCK>',
    variable_start_string='<<',
    variable_end_string='>>',
    comment_start_string='<#',
    comment_end_string='#>'
)
Resume0Template = jinja_env.get_template('data_samples/Resume0.tex.jinja')
Resume1Template = jinja_env.get_template('data_samples/Resume1.tex.jinja')
Resume2Template = jinja_env.get_template('data_samples/Resume2.tex.jinja')
Resume3Template = jinja_env.get_template('data_samples/Resume3.tex.jinja')

# --- Nested Link Structures ---
class LinkData(BaseModel):
    href: str = Field(description="Full URL string")
    text: str = Field(description="Display text or username")

# --- Static Profile Components ---
class Education(BaseModel):
    institution: str
    location: str
    degree: str
    date: str
    grade: Optional[str] = None

class Certification(BaseModel):
    name: str
    issuing_organization: Optional[str] = None
    link: str

class StaticProfile(BaseModel):
    fullname: str = Field(..., description="Full name of the candidate") # Fixed key name
    location: str
    phone: str
    email: LinkData
    linkedin: LinkData
    github: LinkData
    portfolio: LinkData
    education: List[Education]
    certifications: List[Certification]

# --- Tailored Jobs Components ---
class SkillValue(BaseModel):
    name: str
    level: str
    score: float

class SkillCategory(BaseModel):
    category: str
    values: List[SkillValue]

class Project(BaseModel):
    name: str
    project_line: str
    href: Optional[str] = None
    href_name: Optional[str] = None
    points: List[str]

class Achievement(BaseModel):
    name: str
    description: str

class Experience(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    title: str = Field(..., alias="Title")
    company: str
    location: str
    date: str
    points: List[str]

class TailoredJob(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    job_index: int
    role: str = Field(..., alias="Role")
    professional_summary: str
    skills: List[SkillCategory]
    projects: List[Project]
    experience: List[Experience]
    achievements: List[Achievement] = Field(default_factory=list)

# --- Master Schema ---
class Format(BaseModel):
    static_profile: StaticProfile
    tailored_jobs: List[TailoredJob]


# ╭── Gemini setup ───────────────────────────────────────────────╮
if not GOOGLE_API:
    raise ValueError("Set GOOGLE_API env var")
client = genai.Client(api_key=GOOGLE_API)
model_1 = 'gemini-2.5-flash'
model_2 = 'gemini-2.5-flash-lite'
model_3 = "gemini-3.1-flash-lite"  # UNVERIFIED id — kept out of MODELS until confirmed valid
# Ordered fallback list for retries. Only verified ids: a bad id 400s on every
# attempt and (since the error filter below now also catches it) burns the whole
# retry budget. Re-add model_3 here once confirmed against the live Gemini catalog.
MODELS = [model_1, model_2]
# client = Groq(
#     api_key=GROQ_API,
# )
# model="groq/compound"

# ╰───────────────────────────────────────────────────────────────╯

# ╭── Resume-text helpers ────────────────────────────────────────╮
def _pdf_to_txt(r):
    pdf_bytes = r.content  # bytes of PDF from requests response

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    raw_url_regex = re.compile(r'https?://[^\s]+|www\.[^\s]+')

    for page_num, page in enumerate(doc):
        # 1. Fallback to OCR if page has no standard text layer
        text_blocks = page.get_text("blocks")
        has_text = any(b[4].strip() for b in text_blocks)

        if not has_text:
            try:
                ocr_page = page.get_textpage_ocr(flags=3, language="eng", dpi=300)
                text_blocks = ocr_page.extractBLOCKS()
            except Exception as e:
                print(f"[Warning] OCR failed on page {page_num + 1}: {e}", file=sys.stderr)
                text_blocks = []

        # 2. Map links to their exact text block using spatial coordinates
        page_links = page.get_links()
        page_output = []

        if text_blocks:
            for block in text_blocks:
                bx0, by0, bx1, by1, block_content, _, _ = block
                clean_content = block_content.strip()

                if not clean_content:
                    continue

                # Find links that overlap with this specific block's boundary box
                matched_links = []
                for link in page_links:
                    if "uri" in link:
                        lx0, ly0, lx1, ly1 = link["from"]
                        # Check collision/intersection
                        if (bx0 <= lx1 and bx1 >= lx0 and by0 <= ly1 and by1 >= ly0):
                            url = link["uri"].strip()
                            # Grab text strictly inside the link's bounding box
                            anchor_text = page.get_text("text", clip=link["from"]).strip()
                            anchor_clean = anchor_text.strip(" :,.-•[]()")
                            
                            if anchor_clean and not raw_url_regex.search(anchor_clean):
                                matched_links.append((anchor_clean, url))

                # 3. Process links locally inside the text block to prevent global overlap errors
                if matched_links:
                    # Sort matched links right-to-left or bottom-to-top to avoid offset shifting issues
                    for anchor, url in sorted(matched_links, key=lambda x: len(x[0]), reverse=True):
                        # Construct key-value format
                        replacement = f"{anchor}: {url}"
                        
                        # Replace only the FIRST occurrence within this specific paragraph block
                        # This safely splits up duplicate links like "[Link]" across multiple rows
                        if anchor in clean_content and f": {url}" not in clean_content:
                            clean_content = clean_content.replace(anchor, replacement, 1)

                page_output.append(clean_content)

        full_text += "\n".join(page_output) + "\n\n"

    doc.close()
    return full_text

def extract_resume_text(url: str) -> str:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    ct = r.headers.get("Content-Type", "").lower()
    if "pdf" in ct or url.lower().endswith(".pdf"):
        return _pdf_to_txt(r)
    raise ValueError("Unsupported resume format")
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Prompt builder ─────────────────────────────────────────────╮

SYSTEM_INSTRUCTIONS = r"""

    You are an elite, AI-powered ATS Resume Strategist. Your function is to parse a candidate's raw resume text and strategically tailor it to each target Job Description (JD) provided. You must output the result strictly as a single, valid JSON object that conforms to the response schema.

    --- OUTPUT FORMAT ---

    1. RAW TEXT ONLY: Emit plain, human-readable text in every string field. Do NOT escape any characters for LaTeX, Markdown, or HTML (no backslashes before &, %, $, #, _, {, }, ~, ^). Downstream code performs all escaping; pre-escaping will corrupt the rendered resume. The only exception is JSON's own required escaping (e.g. \" inside a string).
    2. EXACT JOB COUNT: Generate exactly N entries in the `tailored_jobs` array, where N equals the number of <JOB_DESCRIPTION> blocks provided. Each entry's `job_index` MUST match its JOB number (1-indexed).

    --- CRITICAL GUARDRAILS (ZERO HALLUCINATION) ---

    3. ABSOLUTE TRUTH: You are strictly forbidden from inventing, fabricating, assuming, or extrapolating ANY skills, experiences, job titles, companies, degrees, dates, or URLs not explicitly present in the candidate's <EXTRACTED_PDF_TEXT>.
    4. NO PLACEHOLDERS: If a contact detail, link (GitHub, LinkedIn, Portfolio), or section is missing from the resume, return an empty string "" or null for that field. Never output placeholder text like "your.email@example.com" or "github.com/username".
    5. STRICT DATA SEPARATION:
       - "Work Experience" means formal corporate employment only (full-time, part-time, or internships).
       - "Projects" are academic, personal, hackathon, or open-source builds.
       - If the candidate has NO formal work experience, the `experience` array MUST be empty: `[]`. Never push personal projects into the experience array.

    --- MANDATORY COMPLETENESS RULES ---

    6. ALL PROJECTS: Include EVERY project from the resume in each tailored_jobs entry — never omit any. Reorder them by relevance to that JD (most relevant first).
    7. ALL EXPERIENCE: If the candidate has work experience, include ALL entries in each tailored_jobs entry, reordered by relevance to that JD. If none exists, return `[]`.
    8. ALL SKILLS: Include ALL technical skills from the resume, grouped into logical categories (e.g. "Languages", "Backend & AI", "Frontend", "Database & Infra", "Tools & Frameworks"). Do NOT cherry-pick only JD-relevant skills; within each category, order the JD-relevant skills first.

    --- STRATEGIC TAILORING RULES ---

    9. SUMMARY: Rewrite `professional_summary` for each JD to foreground the candidate's existing strengths that match that JD's core requirements. Max 430 characters, 2-3 sentences, metric-driven and punchy.
    10. BULLET POINTS: Each project and each experience entry must have EXACTLY 3 bullet points. Every bullet is one line of roughly 10-15 words, starts with a strong action verb, and emphasizes accomplishments, tech stacks, and methodologies relevant to the target JD. Draw only from the candidate's real content — never invent responsibilities or technologies.
    11. SKILL SCORING (proficiency, NOT relevance): For every skill assign:
       - `level`: one of "Beginner", "Intermediate", "Advanced", "Expert".
       - `score`: a float 0.1-1.0 reflecting PROFICIENCY ONLY. Assign 0.8-1.0 if the skill is used across multiple complex projects or core employment; 0.5-0.7 if mentioned once or in a minor project; if ambiguous, default to "Intermediate" / 0.7. Express JD-relevance through ordering (rule 8), never by lowering a skill's score.
    12. ACHIEVEMENTS: If the resume contains achievements (awards, honors, recognitions), add each to the `achievements` array as { "name": <short title>, "description": <one concise sentence pitching its relevance for ATS> }. Route hackathons to `projects` (per rule 5), not here.

"""

def build_prompt(original_resume: str, jobs: List[str]) -> str:

    prompt_parts = [
        SYSTEM_INSTRUCTIONS,
        "\n## User Data and Job Descriptions",
        "<EXTRACTED_PDF_TEXT>",
        original_resume,
        "</EXTRACTED_PDF_TEXT>"
    ]

    # Add each job description in a structured format
    for i, jd in enumerate(jobs, 1):
        prompt_parts.append(f"\n=== JOB {i} ===")
        prompt_parts.append("<JOB_DESCRIPTION>")
        prompt_parts.append(jd)
        prompt_parts.append("</JOB_DESCRIPTION>")

    return "\n".join(prompt_parts)
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Gemini call ------------------------------------------------╮
class TruncatedOutputError(Exception):
    """Structured output came back unparseable/truncated. Retrying the identical
    over-budget prompt is futile — the caller (tailor_jobs) should split instead."""


def ask_gemini(orig: str, jobs: List[str]) -> Format:
    prompt = build_prompt(orig, jobs)
    # Start with first model and move through MODELS on specific failures
    model_idx = 0
    choose_model = MODELS[model_idx]
    for attempt, delay in zip(range(1, 6), (0, 5, 10, 5, 10)):
        try:
            log.info("Gemini - (%s) attempt %d/5", choose_model, attempt)
            # txt = client.chat.completions.create(
            #     messages=[
            #         {
            #             "role": "system",
            #             "content": "no preamble just give the proper Latex code without any explainations, your response should start with ```latex and end with ```."
            #             "***Code shouldn't have any syntax errors proper tailored latex code should be provide.***"
            #         },
            #         {
            #             "role": "user",
            #             "content": prompt,
            #         }
            #     ],
            #     model=model,
            # )
            res = client.models.generate_content(
                model=choose_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema= Format,
                    # Model max (Gemini 2.5 Flash = 65536). One call must be able to
                    # hold all N resumes; an unset/low cap truncates the structured
                    # JSON -> .parsed is None -> the whole batch falls back to the
                    # untailored original PDF. Billed on actual output, so the high
                    # ceiling costs nothing unless used.
                    max_output_tokens=65536,
                )
            ).parsed

            if res is None:
                # Truncated / unparseable. Don't retry the identical over-budget prompt —
                # surface immediately so tailor_jobs splits the batch instead.
                raise TruncatedOutputError("Gemini returned no parseable structured output (likely truncated)")

            log.debug("Gemini preview: %s", res.model_dump_json(indent=2)[:300].replace("\n", " ↩ "))
            return res
        except TruncatedOutputError:
            raise
        except Exception as e:
            # Switch model on quota/availability/invalid-model errors. INVALID_ARGUMENT
            # / 400 / NOT_FOUND catch a bad model id so it doesn't burn every retry slot.
            if any(code in str(e) for code in ("404", "429", "503", "400", "INVALID_ARGUMENT", "NOT_FOUND")):
                if model_idx < len(MODELS) - 1:
                    model_idx += 1
                    choose_model = MODELS[model_idx]
                    log.warning("Switching model due to error (%s) → %s", e, choose_model)
                else:
                    log.warning("Already on last fallback model (%s); will retry", choose_model)
            else:
                log.error("Gemini error: %s", str(e))
            # Jittered backoff so concurrent free-tier workers don't thundering-herd the quota.
            time.sleep(delay + random.uniform(0, 1.0))
            continue
    raise RuntimeError("Gemini failed after retries")
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Adaptive batch tailoring ───────────────────────────────────╮
def tailor_jobs(orig: str, jds: List[str], offset: int = 0) -> Format:
    """Tailor N job descriptions in ONE Gemini call when it fits the output budget.

    On truncation / short return / call failure, split the list and retry each
    half recursively. `job_index` in the returned Format is GLOBAL: offset+1 ..
    offset+len(jds), matching the 1-indexed position used by `_split`/`process_batch`.

    Positions that could not be tailored are simply ABSENT from `tailored_jobs`
    (the caller falls back to the original PDF for those, per-job). Raises only if
    NOTHING in `jds` could be tailored — so a single bad job never sinks the batch.
    """
    n = len(jds)
    try:
        res = ask_gemini(orig, jds)
        got = list(res.tailored_jobs)
        if n == 1:
            # Single job is unambiguous: there is exactly one JD, so force the one
            # returned entry into this slot regardless of how the model labeled it.
            if got:
                got[0].job_index = offset + 1
                res.tailored_jobs = [got[0]]
                return res
        else:
            # Place each entry by its OWN model label (global slot = offset + label) —
            # but ONLY if the labels are a clean permutation of 1..n. A duplicate, gap,
            # wrong count, or out-of-range label means we cannot trust which JD an entry
            # belongs to; splitting is safer than risking a resume rendered for the wrong
            # job. The split eventually isolates jobs down to the n==1 case above, which
            # is always correctly placed.
            labels = sorted(tj.job_index for tj in got)
            if len(got) == n and labels == list(range(1, n + 1)):
                for tj in got:
                    tj.job_index = offset + tj.job_index
                res.tailored_jobs = got
                return res
            log.warning("ask_gemini returned indices %s for n=%d (offset %d); splitting",
                        labels, n, offset)
    except Exception as e:
        log.warning("ask_gemini failed for %d jobs (offset %d): %s; splitting", n, offset, e)

    if n == 1:
        raise RuntimeError(f"Failed to tailor job at offset {offset}")

    mid = n // 2
    static = None
    merged: List[TailoredJob] = []
    left_err = right_err = None
    try:
        left = tailor_jobs(orig, jds[:mid], offset)
        static = static or left.static_profile
        merged.extend(left.tailored_jobs)
    except Exception as e:
        left_err = e
    try:
        right = tailor_jobs(orig, jds[mid:], offset + mid)
        static = static or right.static_profile
        merged.extend(right.tailored_jobs)
    except Exception as e:
        right_err = e

    if static is None:
        raise RuntimeError(
            f"Failed to tailor jobs at offset {offset} (n={n}): left={left_err}; right={right_err}"
        )
    return Format(static_profile=static, tailored_jobs=merged)
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Parsing helpers ────────────────────────────────────────────╮
def escape_latex(s: str) -> str:
    if not isinstance(s, str):
        return s
    return (s.replace("\\", "\\textbackslash ")
            .replace("&", "\\&")
            .replace("%", "\\%")
            .replace("$", "\\$")
            .replace("#", "\\#")
            .replace("_", "\\_")
            .replace("{", "\\{")
            .replace("}", "\\}")
            .replace("~", "\\textasciitilde ")
            .replace("^", "\\textasciicircum "))

from pydantic import BaseModel

def escape_pydantic(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = escape_pydantic(obj[i])
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k not in ('href', 'link', 'job_url'):
                obj[k] = escape_pydantic(v)
    elif isinstance(obj, BaseModel):
        for field_name in type(obj).model_fields.keys():
            if field_name not in ('href', 'link', 'job_url'):
                val = getattr(obj, field_name)
                setattr(obj, field_name, escape_pydantic(val))
    elif isinstance(obj, str):
        return escape_latex(obj)
    return obj

def _split(text: Format, job_index: int, template: int = 0) -> str:
    """Find tailored job by job_index (1-indexed) and render with the chosen template."""
    dynamic_data = None
    for tj in text.tailored_jobs:
        if tj.job_index == job_index:
            dynamic_data = tj
            break

    if dynamic_data is None:
        log.error("Job index %d not found in Gemini response (got indices: %s)",
                  job_index, [tj.job_index for tj in text.tailored_jobs])
        return None

    render_context = {
        "static_profile": text.static_profile,
        "job": dynamic_data
    }

    templates = {
        0: Resume0Template,
        1: Resume1Template,
        2: Resume2Template,
        3: Resume3Template,
    }
    chosen = templates.get(template, Resume0Template)
    rendered = chosen.render(render_context)
    # Debug dump only when explicitly enabled, and never let a write failure
    # (e.g. read-only/ephemeral Cloud Run FS) propagate into the render result.
    if os.getenv("TAILOR_DEBUG"):
        try:
            with open("tailored_resumes.txt", "a", encoding="utf-8") as f:
                f.write(rendered)
        except Exception as e:
            log.debug("TAILOR_DEBUG render dump skipped: %s", e)
    return rendered

# ╰───────────────────────────────────────────────────────────────╯

# ╭── LaTeX handling ─────────────────────────────────────────────╮
ENGINES = [
    ("ytotech", "https://latex.ytotech.com/builds/sync", "orig"),
    ("latexonline", "https://latexonline.cc/compile", "orig"),
    ("api.online", "https://api.latexonline.cc/compile", "orig"),
    ("texlive", "https://texlive.net/run", "texlive"),
    ("codecogs", "https://latex.codecogs.com/pdf.download", "direct")
]
def compile_tex(tex: str) -> bytes | None:
    for name, url, m in ENGINES:
        try:
            log.info("Enhanced Tailor agent")
            log.info("Trying %s...", name)  # Show which endpoint we're trying
            if m == "orig":
                r = requests.post(url, files={"texfile": ("main.tex", tex)}, data={"command": "pdflatex"}, timeout=120)
            elif m == "texlive":
                r = requests.post(url, files={"file": ("m.tex", tex)}, data={"format": "pdf", "engine": "pdflatex"}, timeout=120)
            else:
                r = requests.post(url, data=tex, headers={"Content-Type": "application/x-latex"}, timeout=120)

            # Show HTTP status for all responses
            log.info("%s returned HTTP %d", name, r.status_code)

            if 200 <= r.status_code < 300 and r.content.startswith(b"%PDF"):
                log.info("✅ Compiled successfully via %s", name)
                return r.content
            else:
                # Show WHY it failed
                if not r.content.startswith(b"%PDF"):
                    log.warning("❌ %s: Not a valid PDF response", name)
                    try:
                        log.warning("Response preview: %s", r.text[:200])
                    except Exception:
                        log.warning("Response preview: <binary or decode error>")
                else:
                    log.warning("❌ %s: HTTP error %d", name, r.status_code)

        except requests.exceptions.Timeout:
            log.error("❌ %s: Request timed out", name)
        except requests.exceptions.ConnectionError as e:
            log.error("❌ %s: Connection error - %s", name, str(e))
        except Exception as e:
            log.error("❌ %s: Unexpected error - %s", name, str(e))

    log.error("🚫 All LaTeX services failed")
    return None

# ╰───────────────────────────────────────────────────────────────╯

# ╭── Batch processor ────────────────────────────────────────────╮
def process_batch(resume_url: str | None = None, jobs: List[Dict[str, str]] | None = None, user_data: str | None = None, template: int | None = 0 ) -> List[Dict[str, Any]]:
    global _TEMPLATE
    log.info("template from request - %d ", template if template >=0  else "not yet received")
    log.info("Processing %d jobs", len(jobs))
    if template >= 0:
        _TEMPLATE = template
    original_txt = ""
    original_pdf = b""
    if resume_url:
        try:
            original_pdf = requests.get(resume_url, timeout=60).content
        except Exception as e:
            log.error("Failed to download original PDF: %s", str(e))
            raise
        # resume_url is the authoritative tailoring source: always extract the
        # full PDF text. user_data (a thin parsed profile) is only a fallback if
        # extraction fails — otherwise resumes come out incomplete (no projects,
        # no experience bullets, which the JSON profile does not contain).
        try:
            original_txt = extract_resume_text(resume_url)
        except Exception as e:
            log.error("Failed to extract resume text: %s", str(e))
            if user_data:
                log.warning("PDF extract failed; falling back to user_data profile")
                original_txt = user_data
            else:
                raise
    else:
        original_txt = user_data
    try:
        # Adaptive: one Gemini call for the whole batch when it fits the output
        # budget; splits and retries on truncation. Per-job isolation — a single
        # failed job is absent from the result and falls back to its original PDF
        # below, instead of collapsing the whole batch.
        gemini_ans = tailor_jobs(original_txt, [j["job_description"] for j in jobs])
        escape_pydantic(gemini_ans)
    except Exception as e:
        log.error("Gemini failed: %s", str(e))
        # Fallback: treat as all "no changes"
        gemini_ans = "NO_CHANGES_NEEDED"
    out = []
    for i, job in enumerate(jobs):
        try:
            pdf = b""
            if gemini_ans == "NO_CHANGES_NEEDED":
                if original_pdf: 
                    pdf = original_pdf
                    log.debug("Job %d: no changes", i)
            else:
                tex = _split(gemini_ans, i + 1, template)  # job_index is 1-indexed
                pdf = compile_tex(tex) if tex else None
                if not pdf:
                    if original_pdf:
                        pdf = original_pdf
                    else:
                        log.warning("Failed to generate PDF")
                    log.warning("Job %d: fallback to original PDF", i)
            out.append({
                "job_url": job["job_url"],
                "resume_binary": base64.b64encode(pdf).decode(),
                "company_name": job.get("company_name"),
            })
        except Exception as e:
            import traceback
            log.error("Job %d error %s – using original", i, e)
            traceback.print_exc()
            out.append({
                "job_url": job["job_url"],
                "resume_binary": base64.b64encode(original_pdf).decode(),
                "company_name": job.get("company_name"),
            })
    return out
# ╰───────────────────────────────────────────────────────────────╯

# ╭── File helpers & main ────────────────────────────────────────╮
def load_jobs(p: str):
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    jobs = []
    for j in data:
        job_url = j.get("job_url") or j.get("jobUrl")
        job_description = j.get("job_description") or j.get("description")
        if job_url and job_description:
            jobs.append({"job_url": job_url, "job_description": job_description})
    return jobs

def run_all(jfile: str, resume_url: str, batch: int = 15):
    jobs = load_jobs(jfile)
    res = []
    for i in range(0, len(jobs), batch):
        res += process_batch(resume_url, jobs[i:i + batch])
        if i + batch < len(jobs):
            log.debug("Pause 30 s")
            time.sleep(30)
    return res

if __name__ == "__main__":
    RESUME_URL = "https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/1780978571731_SRINIVAS_SAI_SARAN_TEJA_.pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS8xNzgwOTc4NTcxNzMxX1NSSU5JVkFTX1NBSV9TQVJBTl9URUpBXy5wZGYiLCJpYXQiOjE3ODA5Nzg1NzQsImV4cCI6MTc4OTYxODU3NH0.4WukzYj6IZpF49_4E4S4buq06_beMn3Cz_JojgJbhxM"
    JOBS_JSON = "agents/test_data.json"
    OUT = "tailored_resumes_batch_kv.json"
    Path(OUT).write_text(json.dumps(run_all(JOBS_JSON, RESUME_URL), indent=2), encoding="utf-8")
    log.info("Done → %s", OUT)
