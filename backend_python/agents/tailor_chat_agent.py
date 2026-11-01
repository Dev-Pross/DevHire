import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from agents.llm_gateway import gemini_gateway, GatewayError
from agents.tailor import Format, TailoredJob, StaticProfile
from agents.tailor_v2_models import ReviseComment, validate_section_key

log = logging.getLogger("tailor_chat_agent")

REVISE_SYSTEM_PROMPT = """
You are an expert executive resume strategist and precise editor.
Your objective is to revise and tailor SPECIFIC tagged sections of a candidate's resume to align with a target Job Description, strictly adhering to the candidate's instructions.

CRITICAL INVIOLABLE RULES:
1. MANDATORY SECTION COVERAGE:
   - For EVERY entry in USER REVISION INSTRUCTIONS, you MUST output an entry in `updated_sections` matching that exact `section_key`. You MUST NEVER return an empty `updated_sections` list.
   - When `section_key` is "projects", you MUST return the COMPLETE array of all project objects, reordered and re-ranked according to the user's instructions and Job Description relevance.

2. FACTUAL ANCHORING & FROZEN ANCHORS:
   - Organization names, Job Titles, Degree Names, and Institutions are STRICTLY IMMUTABLE.
   - For collection edits ("projects"), you ARE EXPLICITLY REQUIRED TO RE-RANK AND REORDER the projects according to user instruction and JD alignment. Each project in the array must strictly preserve its "name", "project_line", and "href" while re-ranking the array order.
   - For individual item edits (e.g. experience.0, projects.0), you may ONLY modify bullet points.
   - You MUST NOT fabricate companies, degrees, dates, certifications, tools, or metrics that do not exist in the candidate's master history.

3. SECTION SCOPE ISOLATION:
   - Modify ONLY the sections provided in the input payload.
   - Output ONLY the modified data keyed by their exact section keys.
   - Do NOT include conversational filler, markdown formatting outside JSON, or unsolicited changes to other sections.

4. CLEAN TYPOGRAPHY & SYNTAX:
   - The ONLY allowable markdown formatting is `**bold text**` for keyword highlighting.
   - STRICTLY FORBIDDEN: Raw LaTeX commands (\\textbf, \\item, %, &, \\vspace), raw HTML tags, backticks, or emoji.

5. CONCISENESS & LENGTH BUDGET:
   - Maintain concise single-page density. Bullet points must not exceed 2 lines (approx. 160 characters per bullet).
   - Summaries must remain between 2 to 4 sentences maximum.
"""

class SectionUpdateItem(BaseModel):
    section_key: str = Field(description="Exact section key, e.g. 'summary', 'skills', 'experience.0', 'projects.0'")
    revised_json: str = Field(description="JSON serialized string of the revised content for this section (e.g. plain string for summary, list of bullet strings for experience, or JSON object/array).")

class ReviseOutputSchema(BaseModel):
    updated_sections: List[SectionUpdateItem] = Field(
        ...,
        description="List of updated section items."
    )


def extract_sections_for_edit(format_obj: Format, comments: List[ReviseComment]) -> Dict[str, Any]:
    """Extracts only the data for the sections targeted in comments."""
    job = format_obj.tailored_jobs[0] if format_obj.tailored_jobs else None
    static = format_obj.static_profile
    extracted = {}

    for c in comments:
        key = c.section_key
        if key == "summary" and job:
            extracted[key] = job.professional_summary
        elif key == "skills" and job:
            extracted[key] = [s.model_dump() for s in job.skills]
        elif key == "education":
            extracted[key] = [e.model_dump() for e in static.education]
        elif key == "certifications":
            extracted[key] = [cert.model_dump() for cert in static.certifications]
        elif key == "achievements" and job:
            extracted[key] = [a.model_dump() for a in job.achievements]
        elif key == "projects" and job:
            extracted[key] = [p.model_dump() for p in job.projects]
        elif key == "experience" and job:
            extracted[key] = [e.model_dump() for e in job.experience]
        elif key == "header":
            extracted[key] = {
                "fullname": static.fullname,
                "location": static.location,
                "phone": static.phone,
                "email": static.email.model_dump(),
                "linkedin": static.linkedin.model_dump(),
                "github": static.github.model_dump(),
                "portfolio": static.portfolio.model_dump()
            }
        elif key.startswith("experience.") and job:
            idx = int(key.split(".")[1])
            if 0 <= idx < len(job.experience):
                extracted[key] = job.experience[idx].model_dump()
        elif key.startswith("projects.") and job:
            idx = int(key.split(".")[1])
            if 0 <= idx < len(job.projects):
                extracted[key] = job.projects[idx].model_dump()

    return extracted


def _robust_parse_json(val: Any) -> Any:
    """Robustly parses JSON data even if returned as a double-escaped or malformed string."""
    if isinstance(val, (dict, list)):
        return val
    if not isinstance(val, str):
        return val
    val = val.strip()
    if val.startswith("```json"):
        val = val[7:]
    elif val.startswith("```"):
        val = val[3:]
    if val.endswith("```"):
        val = val[:-3]
    val = val.strip()
    # 1. Direct parse
    try:
        return json.loads(val)
    except Exception:
        pass
    # 2. Unescape double-escaped quotes
    try:
        cleaned = val.replace(r'\"', '"').replace(r'\\"', '"')
        return json.loads(cleaned)
    except Exception:
        pass
    # 3. Locate array brackets
    start_sq = val.find("[")
    end_sq = val.rfind("]")
    if start_sq != -1 and end_sq != -1 and end_sq > start_sq:
        try:
            sub = val[start_sq:end_sq+1].replace(r'\"', '"').replace(r'\\"', '"')
            return json.loads(sub)
        except Exception:
            pass
    # 4. Locate object braces
    start_cu = val.find("{")
    end_cu = val.rfind("}")
    if start_cu != -1 and end_cu != -1 and end_cu > start_cu:
        try:
            sub = val[start_cu:end_cu+1].replace(r'\"', '"').replace(r'\\"', '"')
            return json.loads(sub)
        except Exception:
            pass
    return val


def merge_revised_sections(current_format: Format, updated_sections: Dict[str, Any]) -> Format:
    """Merges revised section payloads back into the canonical Format model."""
    format_dict = current_format.model_dump()
    job_dict = format_dict["tailored_jobs"][0]
    static_dict = format_dict["static_profile"]

    for key, new_val in updated_sections.items():
        if key == "summary":
            if isinstance(new_val, str):
                job_dict["professional_summary"] = new_val
            elif isinstance(new_val, dict) and "professional_summary" in new_val:
                job_dict["professional_summary"] = new_val["professional_summary"]

        elif key == "skills":
            if isinstance(new_val, list):
                job_dict["skills"] = new_val

        elif key == "education":
            if isinstance(new_val, list):
                static_dict["education"] = new_val

        elif key == "certifications":
            if isinstance(new_val, list):
                static_dict["certifications"] = new_val

        elif key == "achievements":
            if isinstance(new_val, list):
                job_dict["achievements"] = new_val

        elif key == "projects":
            parsed_proj = _robust_parse_json(new_val)
            proj_list = None
            if isinstance(parsed_proj, list):
                proj_list = parsed_proj
            elif isinstance(parsed_proj, dict):
                if "projects" in parsed_proj and isinstance(parsed_proj["projects"], list):
                    proj_list = parsed_proj["projects"]
                elif "items" in parsed_proj and isinstance(parsed_proj["items"], list):
                    proj_list = parsed_proj["items"]
            if proj_list:
                orig_projects = {p.get("name", "").lower(): p for p in job_dict.get("projects", [])}
                cleaned_projects = []
                for p in proj_list:
                    if isinstance(p, dict):
                        orig_match = orig_projects.get(p.get("name", "").lower())
                        if orig_match:
                            if "href" in orig_match and not p.get("href"):
                                p["href"] = orig_match["href"]
                            if "project_line" in orig_match and not p.get("project_line"):
                                p["project_line"] = orig_match["project_line"]
                        cleaned_projects.append(p)
                if cleaned_projects:
                    job_dict["projects"] = cleaned_projects

        elif key == "experience":
            if isinstance(new_val, list):
                job_dict["experience"] = new_val

        elif key == "header" and isinstance(new_val, dict):
            for k in ["fullname", "location", "phone"]:
                if k in new_val:
                    static_dict[k] = new_val[k]

        elif key.startswith("experience."):
            idx = int(key.split(".")[1])
            if 0 <= idx < len(job_dict["experience"]):
                if isinstance(new_val, dict):
                    # Preserve immutable anchors
                    orig = job_dict["experience"][idx]
                    orig_title = orig.get("Title") or orig.get("title")
                    orig_company = orig.get("company")
                    orig_date = orig.get("date")
                    orig_loc = orig.get("location")
                    orig_id = orig.get("id")

                    new_val["company"] = orig_company
                    new_val["date"] = orig_date
                    if orig_loc:
                        new_val["location"] = orig_loc
                    if orig_id:
                        new_val["id"] = orig_id

                    # Overwrite both casings to prevent alias hijacking
                    new_val["title"] = orig_title
                    if "Title" in new_val:
                        new_val["Title"] = orig_title
                    job_dict["experience"][idx] = new_val

        elif key.startswith("projects."):
            idx = int(key.split(".")[1])
            if 0 <= idx < len(job_dict["projects"]):
                if isinstance(new_val, dict):
                    orig = job_dict["projects"][idx]
                    new_val["name"] = orig["name"]
                    job_dict["projects"][idx] = new_val

    return Format(**format_dict)


def revise_sections_with_llm(
    job_description: str,
    resume_facts: Dict[str, Any],
    tagged_sections: Dict[str, Any],
    comments: List[ReviseComment],
    is_pro: bool = False
) -> Dict[str, Any]:
    """
    Executes a single structured LLM call to revise candidate resume sections.
    Grounded in ResumeFacts and targeted strictly to tagged instructions.
    """
    instructions_payload = [
        {"section_key": c.section_key, "user_instruction": c.instruction}
        for c in comments
    ]

    prompt_content = f"""
TARGET JOB DESCRIPTION:
{job_description}

CANDIDATE MASTER FACTS (VERIFIED GROUND TRUTH):
{json.dumps(resume_facts, indent=2)}

CURRENT CONTENT OF TAGGED SECTIONS:
{json.dumps(tagged_sections, indent=2)}

USER REVISION INSTRUCTIONS:
{json.dumps(instructions_payload, indent=2)}

Return ONLY a JSON matching the ReviseOutputSchema with updated_sections mapping each tagged section key to its revised data.
"""

    log.info("Invoking LLM revise agent for %d section(s) (is_pro=%s)...", len(comments), is_pro)

    response = gemini_gateway.generate(
        contents=prompt_content,
        system_instruction=REVISE_SYSTEM_PROMPT,
        task="tailor_chat",
        schema=ReviseOutputSchema,
        temperature=0.25,
        max_output_tokens=16384,
        is_pro=is_pro
    )

    if not response or not hasattr(response, "updated_sections"):
        raise RuntimeError("LLM Gateway failed to return a valid revision payload.")

    result_dict: Dict[str, Any] = {}
    for item in response.updated_sections:
        val = item.revised_json.strip() if isinstance(item.revised_json, str) else item.revised_json
        result_dict[item.section_key] = _robust_parse_json(val)

    return result_dict
