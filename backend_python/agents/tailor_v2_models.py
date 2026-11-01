import re
from typing import List, Dict, Any, Optional, Tuple, Union
from pydantic import BaseModel, HttpUrl, Field, field_validator
from agents.tailor import Format, TailoredJob, StaticProfile

# Canonical root section identifiers
ROOT_SECTION_KEYS = {
    "header",           # static_profile contact & identity
    "summary",          # tailored_jobs[0].professional_summary
    "skills",           # tailored_jobs[0].skills
    "education",        # static_profile.education
    "certifications",   # static_profile.certifications
    "achievements",     # tailored_jobs[0].achievements
    "projects",         # whole projects array
    "experience",       # whole experience array
}

# Regex pattern for indexed arrays: experience.0, projects.1, etc.
INDEXED_KEY_REGEX = re.compile(r"^(experience|projects)\.(\d+)$")

def validate_section_key(key: str, format_data: Union[Format, dict]) -> Tuple[bool, str]:
    """
    Validates that a given section key exists and is within index bounds for the provided resume data.
    Returns (is_valid, error_message).
    """
    if not isinstance(key, str) or not key.strip():
        return False, "Section key cannot be empty."

    key = key.strip()

    # 1. Root level section check
    if key in ROOT_SECTION_KEYS:
        return True, ""

    # 2. Indexed section check (e.g. experience.0, projects.2)
    match = INDEXED_KEY_REGEX.match(key)
    if not match:
        return False, f"Invalid section key format: '{key}'. Must be one of {ROOT_SECTION_KEYS} or experience.N / projects.N."

    section_type, index_str = match.groups()
    index = int(index_str)

    # Resolve arrays from either Format instance or dict
    if isinstance(format_data, Format):
        if not format_data.tailored_jobs:
            return False, "No tailored jobs found in resume format."
        job = format_data.tailored_jobs[0]
        items = getattr(job, section_type, [])
    elif isinstance(format_data, dict):
        jobs = format_data.get("tailored_jobs", [])
        if not jobs or not isinstance(jobs, list):
            return False, "No tailored jobs array found in resume data."
        items = jobs[0].get(section_type, [])
    else:
        return False, "Unsupported format_data type for section validation."

    if index < 0 or index >= len(items):
        return False, f"Index out of bounds for '{key}'. Total {section_type} count is {len(items)} (valid indices: 0 to {max(0, len(items) - 1)})."

    return True, ""


# --- API Request & Response Models ---

class TailorV2GenerateRequest(BaseModel):
    user_id: str = Field(..., description="Mandatory unique user identifier", min_length=1)
    job_desc: str = Field(..., description="Target job description text", min_length=10)
    resume_url: HttpUrl = Field(..., description="URL to candidate master resume PDF")
    template: int = Field(default=0, description="Resume template index (0 = Classic single-column)", ge=0, le=3)
    is_pro: bool = Field(default=False, description="Whether the user is Pro tier")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_id is strictly required and cannot be blank.")
        return v.strip()


class TailorV2GenerateResponse(BaseModel):
    success: bool = True
    session_id: str
    tailored_json: Format
    revisions_remaining: int
    expires_at: str
    version: int = 1
    banner_message: Optional[str] = None


class ReviseComment(BaseModel):
    section_key: str = Field(..., description="Target section key, e.g. 'summary' or 'experience.0'")
    instruction: str = Field(..., description="Revision instructions for this specific section", min_length=3, max_length=500)


class TailorV2ReviseRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    comments: List[ReviseComment] = Field(..., min_length=1, max_length=10)
    is_pro: bool = Field(default=False, description="Whether the user is Pro tier")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_id is strictly required.")
        return v.strip()


class TailorV2ReviseResponse(BaseModel):
    success: bool = True
    session_id: str
    updated_sections: Dict[str, Any]
    revisions_remaining: int
    version: int
    banner_message: Optional[str] = None
    tailored_json: Optional[Format] = None


class TailorV2SessionResponse(BaseModel):
    success: bool = True
    session_id: str
    tailored_json: Format
    revisions_remaining: int
    expires_at: str
    version: int
    banner_message: Optional[str] = None


class TailorV2ExportRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    tailored_json: Optional[Format] = None
    template: int = Field(default=0, ge=0, le=3)
