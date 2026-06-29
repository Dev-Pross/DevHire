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
from .pdf_utils import extract_pdf_text_from_url
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
    href: str 
    href_name: str = "link"
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


# --- PASS 1: atomic-fact extraction schema ---
# Pass 1 reads the raw resume once (JD-independent) and decomposes it into atomic
# FACTS — fragments, deliberately NOT bullet sentences — so Pass 2 must COMPOSE
# fresh bullets from them and cannot copy the original wording (it never sees it).
class AtomicFact(BaseModel):
    action: str = Field(..., description="1-4 word lowercase verb-noun stem, NO leading capitalized verb, NOT a full sentence, e.g. 'build auth flow'")
    tech: List[str] = Field(default_factory=list, description="Technologies/tools used for THIS action, e.g. ['Flask','JWT']")
    metric: Optional[str] = Field(None, description="The number GLUED to THIS action, e.g. '5K req/day', '<50ms p99', '30% faster'. Keep with its own action; never detach.")
    object: Optional[str] = Field(None, description="What was acted on, e.g. 'user login', 'ingestion pipeline'")
    outcome: Optional[str] = Field(None, description="Neutral result fragment, e.g. 'reduced latency', 'cut manual review'")

class ExperienceFacts(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    # SKELETON (static identity — copied verbatim into Pass 2 output, never tailored)
    title: str = Field(..., alias="Title")
    company: str
    location: str
    date: str
    facts: List[AtomicFact]

class ProjectFacts(BaseModel):
    # SKELETON (static). project_line is rendered by Resume1/2/3 → keep it as a static fact.
    name: str
    project_line: str
    href: str = ""
    href_name: str = "link"
    facts: List[AtomicFact]

class AchievementFact(BaseModel):
    name: str
    raw: str = Field(..., description="Neutral fact fragment; Pass 2 writes the ATS pitch sentence from it.")

class ResumeFacts(BaseModel):
    static_profile: StaticProfile
    skills_raw: List[str] = Field(default_factory=list, description="Flat, de-duplicated skill names — ungrouped and unscored; grouping/scoring happens in Pass 2.")
    experience: List[ExperienceFacts] = Field(default_factory=list)
    projects: List[ProjectFacts] = Field(default_factory=list)
    achievements: List[AchievementFact] = Field(default_factory=list)


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

def extract_resume_text(url: str) -> str:
    r = requests.get(url, timeout=60, stream=True)
    r.raise_for_status()
    ct = r.headers.get("Content-Type", "").lower()
    if "pdf" in ct or url.lower().endswith(".pdf"):
        return extract_pdf_text_from_url(url)
    raise ValueError("Unsupported resume format")
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Prompt builder ─────────────────────────────────────────────╮

# ── PASS 1 prompt: raw resume → atomic facts (JD-INDEPENDENT) ──
# The whole point of two-pass: Pass 1 decomposes the resume into neutral fact
# FRAGMENTS (not sentences). Pass 2 never sees the resume prose, only these facts,
# so it must compose fresh bullets and CANNOT echo the original wording.
EXTRACT_INSTRUCTIONS = r"""

    You are a precise resume fact-extractor. Read the candidate's raw resume in <EXTRACTED_PDF_TEXT> and emit a single valid JSON object conforming to the ResumeFacts schema. You DECOMPOSE; you do not write prose.

    --- OUTPUT FORMAT ---
    1. RAW TEXT ONLY: Emit plain, human-readable text in every string field. Do NOT escape any characters for LaTeX/Markdown/HTML. Downstream code escapes. Only JSON's own escaping applies (e.g. \" inside a string).

    --- ABSOLUTE TRUTH ---
    2. Never invent, infer, or add any skill, fact, metric, company, title, degree, date, or URL not explicitly present in the resume text. If something is absent, use "" / null / [].
    3. NO PLACEHOLDERS: a missing contact/link/section → "" or null. Never output "your.email@example.com" or "github.com/username".

    --- DECOMPOSITION (the critical rule) ---
    4. Break EVERY accomplishment into atomic facts. For each `AtomicFact`:
       - `action`: a 1-4 word lowercase verb-noun STEM with NO leading capitalized action verb and NO full sentence — e.g. "build auth flow", "scrape job listings". Strip connective words; do NOT echo the resume's sentence structure.
       - `tech`: the technologies/tools used for THIS action only.
       - `metric`: the number tied to THIS action, kept INSIDE this same fact (e.g. "5K req/day", "<50ms latency", "30% faster"). Never detach a metric from the action it measures.
       - `object` / `outcome`: optional neutral fragments.
    5. ONE CLAIM PER FACT: if one resume line states two distinct accomplishments, emit two facts. Emit a fact for EVERY distinct claim — INCLUDING formal-employment lines. Do NOT summarize detail away; over-extraction is fine.

    --- STRUCTURE ---
    6. DATA SEPARATION: formal corporate employment (full-time, part-time, internship) → `experience`; academic/personal/hackathon/open-source builds → `projects`. If there is NO formal employment, `experience` MUST be `[]`. Never push projects into experience.
    7. SKELETON FIELDS (extract exactly as written, these are static identity): experience `title`/`company`/`location`/`date`; project `name`/`href`/`href_name`.
    8. `project_line`: ONE neutral factual one-sentence descriptor per project (e.g. "Real-time data ingestion pipeline"). Describe the project; do NOT tailor or embellish.
    9. SKILLS: list ALL skills in `skills_raw`, flat and de-duplicated — no grouping, no scoring (that happens later).
    10. STATIC PROFILE: extract `fullname`, `location`, `phone`, and `email`/`linkedin`/`github`/`portfolio` (each as {href, text}), plus `education[]` and `certifications[]`, exactly as written.
    11. ACHIEVEMENTS: each award/honor/recognition → { "name": <short title>, "raw": <neutral fact fragment> }. Hackathons go to `projects`, not here.

"""

# ── PASS 2 prompt: atomic facts + JDs → tailored resume (per JD) ──
# Input is <EXTRACTED_FACTS> (a ResumeFacts JSON), NOT the resume prose. Output is
# the same `Format` as before, so all downstream code (split, trim, render) is unchanged.
SYNTHESIZE_INSTRUCTIONS = r"""

    You are an elite, AI-powered ATS Resume Strategist. You are given a CLOSED SET of atomic FACTS about one candidate in <EXTRACTED_FACTS>, plus one or more target Job Descriptions (JDs). For each JD you COMPOSE a tailored resume by writing fresh bullets and summary FROM the facts. You must output a single valid JSON object conforming to the response schema.

    --- OUTPUT FORMAT ---

    1. RAW TEXT ONLY: Emit plain, human-readable text in every string field. Do NOT escape any characters for LaTeX, Markdown, or HTML (no backslashes before &, %, $, #, _, {, }, ~, ^). Downstream code performs all escaping; pre-escaping will corrupt the rendered resume. The only exception is JSON's own required escaping (e.g. \" inside a string).
    2. EXACT JOB COUNT: Generate exactly N entries in the `tailored_jobs` array, where N equals the number of <JOB_DESCRIPTION> blocks provided. Each entry's `job_index` MUST match its JOB number (1-indexed).

    --- CRITICAL GUARDRAILS (CLOSED-WORLD, ZERO HALLUCINATION) ---

    3. CLOSED-WORLD OVER FACTS: Every bullet, summary phrase, skill, and achievement you output MUST be derivable from the facts in <EXTRACTED_FACTS> and nothing else. You CANNOT introduce any technology, metric, company, title, outcome, or skill that does not appear in the facts.
       - You MAY combine fragments (action + tech + metric + object + outcome) from the SAME fact into one natural sentence, and reorder/emphasize per the JD.
       - You MUST NOT merge a metric or tech from one fact onto a DIFFERENT fact's action. Keep each number with the action it came from.
       - The original resume sentences are NOT provided here — so write each bullet naturally and fresh from the fragments; there is nothing to copy.
    4. NO PLACEHOLDERS: If a contact detail or link is empty in the facts, keep it empty (""/null). Never invent placeholder text.

    --- COMPOSITION (write the bullets) ---

    5. COMPOSE EACH BULLET FROM FACTS: For every experience entry and every project entry, write bullets by composing that entry's `facts` into JD-tailored sentences. Each bullet:
       - draws on one or more facts of THE SAME entry (never another entry's facts);
       - LEADS with the technology, methodology, or outcome THIS JD emphasizes (chosen from that fact's `tech`/`metric`/`outcome`);
       - starts with a strong action verb; one line, ~10-15 words;
       - states only what the facts support — surface a metric only if the fact carries one.
       Tailor emphasis and ordering to each JD: the same facts should yield visibly different bullets for a backend JD vs a data JD.
    6. ALL ENTRIES (sourcing, not rendering): Rank EVERY experience entry and EVERY project entry by relevance to this JD and include them in that order — never silently drop an entry. If `experience` facts is empty, output `experience: []`. Bullet counts follow the one-page budget in rule 8.
    7. SUMMARY: Write `professional_summary` for each JD from the facts to foreground the strengths that match that JD's core requirements. Max 430 characters, 2-3 sentences, metric-driven and punchy.
    8. ONE-PAGE BUDGET: The resume MUST fit a single page. Use 2-3 bullets per entry, but across ALL experience + project entries combined do NOT exceed ~10 bullets total. Prioritize experience bullets, then fill projects in relevance order until the budget is reached. When space is tight, drop the least-relevant PROJECT bullets — never fabricate, and never drop experience.

    --- SKILLS / ACHIEVEMENTS ---

    9. ALL SKILLS: Include ALL names from `skills_raw`, grouped into logical categories (e.g. "Languages", "Backend & AI", "Frontend", "Database & Infra", "Tools & Frameworks"). Do NOT cherry-pick only JD-relevant skills; within each category, order JD-relevant skills first. Do NOT rename or invent skills.
    10. SKILL SCORING (proficiency, NOT relevance): For every skill assign `level` ∈ {"Beginner","Intermediate","Advanced","Expert"} and `score` ∈ 0.1-1.0 reflecting PROFICIENCY ONLY (0.8-1.0 if used across multiple complex projects/core employment; 0.5-0.7 if mentioned once; default "Intermediate"/0.7 if ambiguous). Express JD-relevance through ordering (rule 9), never by lowering a score.
    11. ACHIEVEMENTS: For each item in the facts' achievements, output { "name": <short title>, "description": <one concise sentence pitching its relevance for ATS, derived from `raw`> }.

    --- STATIC vs TAILORED FIELDS ---

    12. COPY SKELETON FIELDS VERBATIM from the facts, identical across every job — do NOT rephrase or tailor them: `static_profile` (full name, contact, links, education, certifications); each experience's `title`/`company`/`location`/`date`; each project's `name`/`project_line`/`href`/`href_name`; and every skill NAME. Only the bullet arrays (`experience[].points`, `projects[].points`), `professional_summary`, and skill grouping/scoring are generated.

"""

def build_prompt(payload: str, jobs: List[str], mode: str = "synthesize") -> str:
    """Build the prompt for either pass.

    mode="extract"  : `payload` is the raw resume text; `jobs` is ignored (Pass 1 is
                      JD-independent). Produces a ResumeFacts request.
    mode="synthesize": `payload` is the ResumeFacts JSON; JD blocks are appended in the
                      SAME structure as before so tailor_jobs's split parsing is unchanged.
    """
    if mode == "extract":
        return "\n".join([
            EXTRACT_INSTRUCTIONS,
            "\n## Candidate Resume",
            "<EXTRACTED_PDF_TEXT>",
            payload,
            "</EXTRACTED_PDF_TEXT>",
        ])

    prompt_parts = [
        SYNTHESIZE_INSTRUCTIONS,
        "\n## Candidate Facts and Job Descriptions",
        "<EXTRACTED_FACTS>",
        payload,
        "</EXTRACTED_FACTS>",
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


def ask_gemini(payload: str, jobs: List[str], *, schema=Format, mode: str = "synthesize"):
    prompt = build_prompt(payload, jobs, mode)
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
                    response_schema= schema,
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


def extract_facts(original_txt: str) -> "ResumeFacts":
    """PASS 1: decompose the raw resume into atomic facts (JD-independent, ONE call).

    No JD fan-out → no split/recursion. On truncation the TruncatedOutputError
    propagates and the caller (process_batch) falls back to the original PDF, same
    graceful-degradation contract as a failed tailoring call.
    """
    facts = ask_gemini(original_txt, [], schema=ResumeFacts, mode="extract")
    if not facts.experience and not facts.projects:
        log.warning("PASS 1 extracted 0 experience + 0 project entries from a non-empty resume")
    return facts
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Adaptive batch tailoring ───────────────────────────────────╮
def tailor_jobs(facts_json: str, jds: List[str], offset: int = 0) -> Format:
    """Tailor N job descriptions in ONE Gemini call when it fits the output budget.

    On truncation / short return / call failure, split the list and retry each
    half recursively. `job_index` in the returned Format is GLOBAL: offset+1 ..
    offset+len(jds), matching the 1-indexed position used by `process_batch`.

    Positions that could not be tailored are simply ABSENT from `tailored_jobs`
    (the caller falls back to the original PDF for those, per-job). Raises only if
    NOTHING in `jds` could be tailored — so a single bad job never sinks the batch.
    """
    n = len(jds)
    try:
        res = ask_gemini(facts_json, jds)
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
        left = tailor_jobs(facts_json, jds[:mid], offset)
        static = static or left.static_profile
        merged.extend(left.tailored_jobs)
    except Exception as e:
        left_err = e
    try:
        right = tailor_jobs(facts_json, jds[mid:], offset + mid)
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
            .replace("^", "\\textasciicircum ")
            # Appended LAST: the "\\" pass above already ran, so the backslashes we
            # introduce here are not re-escaped. In OT1 (Resume0) a raw "<"/">"
            # ligatures into "¡"/"¿"; \textless{}/\textgreater{} are kernel-robust
            # and need no package. Fixes e.g. "<50ms" rendering as "¡50ms".
            .replace("<", "\\textless{}")
            .replace(">", "\\textgreater{}"))

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

_TEMPLATES = {
    0: Resume0Template,
    1: Resume1Template,
    2: Resume2Template,
    3: Resume3Template,
}

def _render_tex(static_profile, tj, template: int = 0) -> str:
    """Render ONE tailored job into LaTeX with the chosen template."""
    render_context = {"static_profile": static_profile, "job": tj}
    chosen = _TEMPLATES.get(template, Resume0Template)
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


def _trim_one(tj) -> bool:
    """Remove one unit of the LEAST-relevant PROJECT content to reduce height.

    Projects are ranked most-relevant-first, so we trim from the end: drop the last
    project's last bullet, and when a project has no bullets left, drop the project.
    Never touches experience. Returns False when no project content remains to trim.
    """
    projects = getattr(tj, "projects", None) or []
    if not projects:
        return False
    last = projects[-1]
    points = getattr(last, "points", None) or []
    if len(points) > 1:
        last.points = points[:-1]        # drop least-relevant bullet of least-relevant project
    else:
        tj.projects = projects[:-1]      # drop the whole least-relevant project
    return True


def render_one_page(static_profile, tj, template: int = 0, max_trims: int = 6) -> bytes | None:
    """Render -> compile -> guarantee a SINGLE page.

    If the compiled PDF spans more than one page, trim the least-relevant project
    content (see _trim_one) and recompile, up to `max_trims` times. Returns the
    compiled PDF bytes, or None if compilation fails outright (caller then falls
    back to the candidate's original PDF). Extra compiles happen only on overflow.
    """
    pdf = None
    for attempt in range(max_trims + 1):
        tex = _render_tex(static_profile, tj, template)
        pdf = compile_tex(tex)
        if not pdf:
            return None
        try:
            doc = fitz.open(stream=pdf, filetype="pdf")
            pages = doc.page_count
            doc.close()
        except Exception as e:
            log.warning("Page-count check failed (%s); accepting compiled PDF as-is", e)
            return pdf
        if pages <= 1:
            return pdf
        log.info("Resume is %d pages; trimming least-relevant project content (attempt %d/%d)",
                 pages, attempt + 1, max_trims)
        if not _trim_one(tj):
            log.warning("No project content left to trim; returning best-effort %d-page PDF", pages)
            return pdf
    log.warning("Still over one page after %d trims; returning best-effort PDF", max_trims)
    return pdf

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
def process_batch(resume_url: str | None = None, jobs: List[Dict[str, str]] | None = None, user_data: str | None = None, template: int | None = 0, facts: "ResumeFacts | None" = None) -> List[Dict[str, Any]]:
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
        # PASS 1 — fact extraction (JD-independent, one call per resume). The apply
        # pipeline hoists this and passes `facts` so it isn't repeated per batch.
        if facts is None:
            facts = extract_facts(original_txt)
        facts_json = facts.model_dump_json(by_alias=True)
        # PASS 2 — synthesis: one Gemini call for the whole batch when it fits the
        # output budget; splits and retries on truncation. Per-job isolation — a single
        # failed job is absent from the result and falls back to its original PDF below.
        # Pass 2 sees ONLY the facts, never the resume prose, so it cannot copy bullets.
        gemini_ans = tailor_jobs(facts_json, [j["job_description"] for j in jobs])
        # Identity fields are authoritative from the extracted facts — never trust Pass-2
        # regeneration for them. Deep-copy so escape_pydantic doesn't mutate the shared
        # `facts` (which would double-escape across batches in the apply pipeline).
        gemini_ans.static_profile = facts.static_profile.model_copy(deep=True)
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
                # job_index is 1-indexed and matches batch position i+1.
                tj = next((t for t in gemini_ans.tailored_jobs if t.job_index == i + 1), None)
                if tj is None:
                    log.error("Job %d: job_index %d not in Gemini response (got %s)",
                              i, i + 1, [t.job_index for t in gemini_ans.tailored_jobs])
                    pdf = None
                else:
                    # Render + compile + GUARANTEE one page (trim least-relevant project
                    # content and recompile on overflow).
                    pdf = render_one_page(gemini_ans.static_profile, tj, template)
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
 #   RESUME_URL = "https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/1780978571731_SRINIVAS_SAI_SARAN_TEJA_.pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS8xNzgwOTc4NTcxNzMxX1NSSU5JVkFTX1NBSV9TQVJBTl9URUpBXy5wZGYiLCJpYXQiOjE3ODA5Nzg1NzQsImV4cCI6MTc4OTYxODU3NH0.4WukzYj6IZpF49_4E4S4buq06_beMn3Cz_JojgJbhxM"
    RESUME_URL = "https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/1781886631924_SRINIVAS_SAI_SARAN_TEJA%20(2).pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS8xNzgxODg2NjMxOTI0X1NSSU5JVkFTX1NBSV9TQVJBTl9URUpBICgyKS5wZGYiLCJzY29wZSI6ImRvd25sb2FkIiwiaWF0IjoxNzgxODg2NjMyLCJleHAiOjE3OTA1MjY2MzJ9.87ixL2b30Bb-Gm44SvmRgfNnaOi178XjelkUKRgIoBA"
    JOBS_JSON = "agents/test_data.json"
    OUT = "tailored_resumes_batch_kv.json"
    Path(OUT).write_text(json.dumps(run_all(JOBS_JSON, RESUME_URL), indent=2), encoding="utf-8")
    log.info("Done → %s", OUT)
