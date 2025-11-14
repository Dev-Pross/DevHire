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
import re
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any
import fitz
import requests                       # PyMuPDF / HTTP
from pdf2image import convert_from_bytes
import pytesseract
import google.generativeai as genai
from google.api_core import exceptions as g_exc
from config import GOOGLE_API

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
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Gemini setup ───────────────────────────────────────────────╮
if not GOOGLE_API:
    raise ValueError("Set GOOGLE_API env var")
genai.configure(api_key=GOOGLE_API)
model = genai.GenerativeModel("gemini-2.5-flash") # gemini-2.5-flash-lite
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Resume-text helpers ────────────────────────────────────────╮
def _pdf_to_txt(r):
    pdf_bytes = r.content  # bytes of PDF from requests response

    # Open PDF document from bytes in memory
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    num_pages = len(doc)

    for page_num in range(num_pages):
        page = doc.load_page(page_num)
        page_text = page.get_text().strip()
        if page_text:
            text += page_text + "\n\n"
        else:
            # Fallback to OCR using pdf2image + pytesseract on page bytes
            # Convert only the page to image
            images = convert_from_bytes(pdf_bytes, first_page=page_num + 1, last_page=page_num + 1)
            if images:
                ocr_text = pytesseract.image_to_string(images[0])
                text += ocr_text + "\n\n"
            else:
                log.warning(f"No image generated for PDF page {page_num + 1}")

    doc.close()
    return text

def _docx_to_txt(r):
    pdf_bytes = requests.get(r, timeout=60).content
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = page.get_text()
        if not page_text.strip():
            # Fallback to OCR if no text found
            images = convert_from_bytes(pdf_bytes, first_page=page_num+1, last_page=page_num+1)
            ocr_text = pytesseract.image_to_string(images[0])
            text += ocr_text + "\n\n"
        else:
            text += page_text + "\n\n"
    return text

def extract_resume_text(url: str) -> str:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    ct = r.headers.get("Content-Type", "").lower()
    if "pdf" in ct or url.lower().endswith(".pdf"):
        return _pdf_to_txt(r)
    raise ValueError("Unsupported resume format")
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Prompt builder ─────────────────────────────────────────────╮
_SAMPLE = r"""
\documentclass[a4paper,12pt]{article}

\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjusted margins for proper whitespace
\addtolength{\oddsidemargin}{-0.3in}
\addtolength{\evensidemargin}{-0.3in}
\addtolength{\textwidth}{0.6in}
\addtolength{\topmargin}{-0.4in}
\addtolength{\textheight}{0.8in}

% Formatting for section titles
\titleformat{\section}{%
  \scshape\raggedright\large
}{}{0em}{}[\titlerule]

\newcommand{\resumeItem}[1]{\item\small{{#1}}}

% Subheading for education (4 args)
\newcommand{\resumeSubheading}[4]{\vspace{2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      {\bfseries #1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{2pt}
}

% Project heading (2 args)
\newcommand{\resumeProjectHeading}[2]{\item
  \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
    {\bfseries #1} & \textit{#2} \\
  \end{tabular*}\vspace{2pt}
}

\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=0.2in]}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{6pt}}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}\vspace{8pt}}
\newcommand{\resumeSubHeadingListEndNoSpace}{\end{itemize}\vspace{4pt}}

\begin{document}

%----------HEADING----------
\begin{center}
    {\Huge \bfseries Budumuru Srinivas Sai Saran Teja} \\ \vspace{3pt}
    Visakhapatnam, India $|$ +91 7993027519 $|$ \href{mailto:tejabudumuru3@gmail.com}{tejabudumuru3@gmail.com} \\
    \href{https://linkedin.com/in/teja-budumuru-15123a292}{LinkedIn} $|$ 
    \href{https://github.com/TejaBudumuru3}{GitHub}
\end{center}

%-----------PROFESSIONAL SUMMARY-----------
\section{Professional Summary}
\resumeSubHeadingListStart
\resumeItem{
Enthusiastic Software Developer with proven experience in designing and implementing \textbf{end-to-end applications} across web and desktop platforms. Proficient in \textbf{React.js, Node.js, Express.js, MongoDB, Python, and Java}, with expertise in RESTful API design, authentication, and scalable architectures. Strong understanding of \textbf{OOP, algorithms, database management, and MVC frameworks}. Recognized for building projects that combine innovation and practicality, from AI-driven content generators to automation platforms for recruitment and faculty performance tracking.
}
\resumeSubHeadingListEnd


%-----------TECHNICAL SKILLS-----------
\section{Technical Skills}
\resumeItemListStart
  \resumeItem{\textbf{Programming Languages:} JavaScript (ES6+), Python, Java, SQL}
  \resumeItem{\textbf{Frontend:} React.js, Redux, HTML5, CSS3}
  \resumeItem{\textbf{Backend:} Node.js, Express.js, REST APIs}
  \resumeItem{\textbf{Databases and Automation tools:} MongoDB, MySQL, Supabase and Playwright}
  \resumeItem{\textbf{Version Control:} Git, GitHub}
  \resumeItem{\textbf{Concepts:} OOP, Data Structures, DBMS, MVC architecture, Agile, Clean Code Practices}
  \resumeItem{\textbf{Soft Skills:} Problem Solving, Quick Learning, Effective Communication, Team Collaboration}
\resumeItemListEnd

%-----------EDUCATION-----------
\section{Education}
\resumeSubHeadingListStart
  \resumeSubheading
    {MVGR College of Engineering (A)}{Vizianagaram, India}
    {B.Tech in Computer Science; GPA: 7.48/10}{May 2025}
  \resumeSubheading
    {Government Polytechnic College}{Anakapalle, India}
    {Diploma in Computer Engineering; Final Grade: 82.09\%}{June 2022}
\resumeSubHeadingListEnd

%-----------PROJECTS-----------
\section{Projects}
\resumeSubHeadingListStart

\resumeProjectHeading
    {HireHawk – Fullstack Job Automation}{Ongoing}
    \resumeItemListStart
      \resumeItem{Conceptualized and developing an \textbf{AI-powered recruitment automation platform} aimed at reducing manual effort in job applications.}
      \resumeItem{Designed workflows for \textbf{resume parsing, intelligent job matching, and auto-apply mechanisms}, allowing candidates to apply across multiple portals with minimal effort.}
      \resumeItem{Building backend services with \textbf{Python, Next.js, Supabase} to manage job applying, tailoring resumes, and finding relavent jobs.}
      \resumeItem{Building agents to maintain proper flow from finding titles to applying jobs using automation tool called \textbf{Playwright} in Python to create 4 agents called \textbf{Titles extraction, Scraping relavent jobs, Tailoring resume, Apply agent}}
    \resumeItemListEnd

\resumeProjectHeading
    {Ainfity – AI-Powered Post Generator}{{\href{https://post-generator-iota.vercel.app/}{post-generator-iota.vercel.app}}}
    \resumeItemListStart
      \resumeItem{Developed a \textbf{MERN stack application} that generates AI-driven text and image content for social media posts, helping creators save time.}
      \resumeItem{Implemented \textbf{RESTful APIs} using Express.js and MongoDB with nested JSON schemas for structured data handling.}
      \resumeItem{Integrated \textbf{JWT-based authentication} for secure user sessions and scalable user management.}
      \resumeItem{Designed a responsive \textbf{React.js frontend}, ensuring smooth experience across mobile and desktop devices.}
      \resumeItem{Optimized performance by modularizing backend architecture and adopting Agile practices for rapid iteration.}
    \resumeItemListEnd

\resumeProjectHeading
    {Faculty Performance Monitor}{}
    \resumeItemListStart
      \resumeItem{Developed a \textbf{Java-based web portal} using JSP and MySQL for tracking faculty workload and performance scores.}
      \resumeItem{Implemented role-based access controls, enabling administrators to assign credits and generate evaluation reports.}
      \resumeItem{Applied \textbf{MVC architecture} to ensure clean separation of logic, improving maintainability and scalability.}
      \resumeItem{Optimized SQL queries to improve reporting efficiency and ensure quick data retrieval for administrators.}
    \resumeItemListEnd

\resumeProjectHeading
    {Employee Management System}{}
    \resumeItemListStart
      \resumeItem{Created a \textbf{Python desktop application} with Tkinter GUI and MySQL backend for automating employee payroll processes.}
      \resumeItem{Developed modules for \textbf{salary computation, tax deduction, and employee record management}.}
      \resumeItem{Implemented validation and exception handling to ensure reliable data storage and reduce errors in payroll.}
      \resumeItem{Minimized manual intervention, thereby reducing processing time and improving organizational efficiency.}
    \resumeItemListEnd

\resumeSubHeadingListEnd

%-----------CERTIFICATIONS-----------
\section{Certifications}
\resumeSubHeadingListStart
\resumeItem{AI and Machine Learning -- AICTE}
\resumeItem{Cloud Computing -- NPTEL}
\resumeItem{Java JUnit -- Infosys SpringBoard}
\resumeItem{Foundations of Artificial Intelligence -- SkillUp}
\resumeSubHeadingListEnd

%-----------ACHIEVEMENTS-----------
\section{Achievements}
\resumeItemListStart
  \resumeItem{Participated in Pega Systems Hackathon, demonstrating innovation, problem-solving, and teamwork skills.}

  \resumeItem{Recognized for artistic achievements in drawing competitions (early academic years).}
\resumeItemListEnd

%-----------LANGUAGES-----------
\section{Languages}
\resumeSubHeadingListStart
  \resumeItem{\textbf{English:} Advanced}
  \resumeItem{\textbf{Telugu:} Native Proficiency}
\resumeSubHeadingListEndNoSpace

\end{document}


"""

SYSTEM_INSTRUCTIONS = r"""
You are an expert, AI-powered career strategist and LaTeX document engineer. Your primary function is to transform a standard resume into a highly optimized, ATS-friendly document tailored specifically for a target job description. You will achieve this by following a strict, programmatic algorithm that involves parsing unstructured text, strategically rewriting content, and generating flawless LaTeX code.

This prompt provides detailed explanations for each step. Understanding the 'why' behind each rule is crucial for executing the task perfectly.

---
## Core Directives

**Purpose**: To establish the fundamental principles that govern your entire operation.

1.  **Parse and Structure First**: Your initial and most critical task is to convert the unstructured, messy text from a PDF into a clean, structured internal representation. You cannot tailor content you do not understand.
    * **Rationale**: PDF text extraction is imperfect. Raw text will have random line breaks and spacing. You must intelligently group this text into logical resume sections (Summary, Skills, Projects, etc.) before any tailoring can begin.

2.  **Tailor with Precision and Honesty**: You will strategically rewrite specific sections of the resume to align with the job description. However, you must never invent skills or experiences the candidate does not possess. Your goal is to highlight existing qualifications, not to fabricate new ones.
    * **Rationale**: Honesty is paramount. While the goal is to pass ATS scans, the resume must be a truthful representation of the candidate for the human hiring manager who will read it next.

3.  **Reconstruct with Flawless Code**: The final output must be a syntactically perfect LaTeX document formatted according to the provided template.
    * **Rationale**: The end product is code. It must compile without errors. All data, especially reconstructed hyperlinks, must be correctly formatted within the LaTeX structure.

---
## Generation Algorithm: EXECUTE EXACTLY

**Purpose**: To provide a sequential, step-by-step program. Following this algorithm precisely prevents errors and ensures all requirements are met in the correct order.

**Step 1: Parse and Structure the Raw PDF Text**
- **Task**: Read the `<EXTRACTED_PDF_TEXT>`. Intelligently identify and group the text into logical sections: Name, Contact Info, Professional Summary, Education, Technical Skills, Projects, Work Experience (if any), Certifications, Achievements, and Languages.
- **Rationale**: This creates a clean, structured "database" of the candidate's information that you can work with in the following steps. This is the foundation upon which everything else is built.

**Step 2: Analyze the Job Description and Extract Keywords**
- **Task**: Read the `<JOB_DESCRIPTION>` and identify the top 5-10 most important keywords. These are typically specific technologies (e.g., 'Python', 'React', 'AWS'), methodologies ('Agile', 'Scrum'), or responsibilities ('scalable architectures', 'API integration') which are align with Job description.
- **Rationale**: To tailor a resume effectively, you must first know what the target is. This keyword list becomes your "checklist" for the tailoring process in Step 5.

**Step 3: Reconstruct Static Sections and Hyperlinks**
- **Task**: Using your parsed data from Step 1, build the sections of the resume that do not need tailoring. This includes Education, Certifications, Achievements, and Languages. Most importantly, reconstruct the contact information and any project hyperlinks.
    - **For Contact Info**: The text will mention "LinkedIn" and "GitHub". You MUST use the following known URLs for this user to create the hyperlinks for:
        - LinkedIn: `\href{https://linkedin.com/in/user}{LinkedIn}`
        - GitHub: `\href{https://github.com/user}{GitHub}`
    - **For Projects**: If the parsed text contains a full URL, reconstruct it using an `\href` command.
- **Rationale**: Handling the static, unchangeable parts of the resume first simplifies the process. Explicitly reconstructing URLs from known data is critical because this information is often lost or mangled during PDF text extraction.

** Step 4: Analyze Experience Level **

- **Task**: Based on the parsed sections from Step 1, determine if a "Work Experience" or "Employment History" section exists. "Projects" alone does not count as professional experience. If a valid section exists, classify the user as "Experienced". Otherwise, classify as "Fresher".

- **Rationale**: This classification is critical for choosing the correct resume structure in the next step.

** Step 5: Define Section Order ** 

- **Task**: Based on the classification from Step 4, select the appropriate section order for the final document.

    - **Fresher**: Heading, Professional Summary, Education, Technical Skills, Projects, Certifications, Achievements, Languages.

    - **Experienced**: Heading, Professional Summary, Technical Skills, Work Experience, Projects, Education, Certifications.

- **Rationale**: This step ensures the final layout is professional and highlights the most important information first, depending on the candidate's career level.

** Step 6: Execute ATS-Friendly Content Tailoring **

- **Task**: Rewrite the dynamic sections using the keyword list from Step 2 as your guide.

    - 1. Professional Summary: Write a new summary that directly targets the job description.

    - 2. Technical Skills: Ensure the skills section mirrors the keywords from the job description.

    - 3. Projects / Work Experience: Rewrite bullet points to showcase accomplishments that match the job's needs.

- **Rationale**: This is the core creative step, designed for maximum ATS impact.

** Step 7: Assemble Final LaTeX Document **

- **Task**: Construct the final LaTeX file using the <LATEX_TEMPLATE>. Populate it with the tailored content, arranging the sections according to the order you defined in Step 4.

- **Rationale**: This is the final assembly phase, building the document according to the correct, pre-defined structure.
---
## Output Requirements

**Purpose**: To define the strict API contract for your response, ensuring it is machine-readable by the calling application.

1.  **Delimiter**: Start each job's output with `=== JOB {number} ===`.
    * **Rationale**: The delimiter allows the program parsing your output to reliably `split()` the single text stream into multiple, individual results.
2.  **No-Change Condition**: If the resume is already a perfect match, the block must contain only the text `NO_CHANGES_NEEDED`.
    * **Rationale**: This is a clear, simple flag for the parsing program to understand.
3.  **LaTeX Output**: Otherwise, the block must contain the complete, valid LaTeX code, starting with `\documentclass`.
    * **Rationale**: This ensures the output is ready for direct use without further processing."""

def build_prompt(original_resume: str, jobs: List[str]) -> str:

    # Start with the core instructions and the template
    prompt_parts = [
        SYSTEM_INSTRUCTIONS,
        "## LaTeX Template for Formatting (Style Reference Only)",
        "<LATEX_TEMPLATE>",
        _SAMPLE,
        "</LATEX_TEMPLATE>",
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
def ask_gemini(orig: str, jobs: List[str]) -> str:
    prompt = build_prompt(orig, jobs)
    for attempt, delay in zip(range(1, 4), (0, 20, 40)):
        try:
            log.info("Gemini attempt %d/3", attempt)
            txt = model.generate_content(prompt).text.strip()

            # ADD THIS LINE TO SAVE GEMINI RESPONSE:
            # Path(f"gemini_debug_{int(time.time())}.txt").write_text(txt, encoding="utf-8")

            log.debug("Gemini preview: %s", txt[:300].replace("\n", " ↩ "))
            return txt
        except g_exc.ResourceExhausted:
            log.warning("Rate-limited – sleep %ss", delay)
            time.sleep(delay)
        except Exception as e:
            log.error("Gemini error: %s", str(e))
            break
    raise RuntimeError("Gemini failed 3×")
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Parsing helpers ────────────────────────────────────────────╮
def _split(text: str, count: int) -> List[str]:
    seg = re.split(r"===\s*JOB\s+(\d+)\s*===", text)
    blk = {}
    for i in range(1, len(seg), 2):
        try:
            blk[int(seg[i])] = seg[i + 1].strip()
        except (IndexError, ValueError):
            continue
    return [blk.get(n, "") for n in range(1, count + 1)]

def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "").upper()
# ╰───────────────────────────────────────────────────────────────╯

def soften_hboxes(tex: str) -> str:
    """
    Insert \\sloppy and \\setlength{\\emergencystretch}{3em}
    immediately after \\begin{document} if they are not present.
    """
    if "\\sloppy" in tex:
        return tex
    return re.sub(
        r"(\\begin\{document\})",
        r"\1\n\\sloppy\n\\setlength{\\emergencystretch}{3em}",
        tex,
        count=1,
        flags=re.IGNORECASE
    )

# ╭── LaTeX handling ─────────────────────────────────────────────╮
ENGINES = [
    ("ytotech", "https://latex.ytotech.com/builds/sync", "orig"),
    ("latexonline", "https://latexonline.cc/compile", "orig"),
    ("api.online", "https://api.latexonline.cc/compile", "orig"),
    ("texlive", "https://texlive.net/run", "texlive"),
    ("codecogs", "https://latex.codecogs.com/pdf.download", "direct")
]
def compile_tex(tex: str) -> bytes | None:
    tex = soften_hboxes(tex)
    for name, url, m in ENGINES:
        try:
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

def tex_from_block(text: str) -> str | None:
    if "```latex" in text:
        # Extract from markdown block
        parts = text.split("```latex")
        if len(parts) > 1:
            latex_code = parts[1].split("```")[0].strip()
            return latex_code
    start_index = text.find("\\documentclass")
    if start_index != -1:
        return text[start_index:].strip()
    return None
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Batch processor ────────────────────────────────────────────╮
def process_batch(resume_url: str, jobs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    log.info("Processing %d jobs", len(jobs))
    try:
        original_pdf = requests.get(resume_url, timeout=60).content
    except Exception as e:
        log.error("Failed to download original PDF: %s", str(e))
        raise
    try:
        original_txt = extract_resume_text(resume_url)
    except Exception as e:
        log.error("Failed to extract resume text: %s", str(e))
        raise
    try:
        gemini_ans = ask_gemini(original_txt, [j["job_description"] for j in jobs])
    except Exception as e:
        log.error("Gemini failed: %s", str(e))
        # Fallback: treat as all "no changes"
        gemini_ans = "\n".join([f"=== JOB {i+1} ===\nNO_CHANGES_NEEDED" for i in range(len(jobs))])
    blocks = _split(gemini_ans, len(jobs))
    out = []
    for i, (job, blk) in enumerate(zip(jobs, blocks), 1):
        try:
            if not blk or _norm(blk) == "NO_CHANGES_NEEDED":
                pdf = original_pdf
                log.debug("Job %d: no changes", i)
            else:
                tex = tex_from_block(blk)
                pdf = compile_tex(tex) if tex else None
                if not pdf:
                    pdf = original_pdf
                    log.warning("Job %d: fallback to original PDF", i)
            out.append({"job_url": job["job_url"], "resume_binary": base64.b64encode(pdf).decode()})
        except Exception as e:
            log.error("Job %d error %s – using original", i, e)
            out.append({"job_url": job["job_url"], "resume_binary": base64.b64encode(original_pdf).decode()})
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
    RESUME_URL = "https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/SRINIVAS_SAI_SARAN_TEJA%20(1).pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS9TUklOSVZBU19TQUlfU0FSQU5fVEVKQSAoMSkucGRmIiwiaWF0IjoxNzU0Mzc4OTgwLCJleHAiOjE3NTY5NzA5ODB9.1unaMom_BGXfxkvFB95XUMFLw7FOoVzMDBwzrJI8mOs"
    JOBS_JSON = "./linkedin_jobs_fast_2025-08-06_16-43-22.json"
    OUT = "tailored_resumes_batch_kv.json"
    Path(OUT).write_text(json.dumps(run_all(JOBS_JSON, RESUME_URL), indent=2), encoding="utf-8")
    log.info("Done → %s", OUT)
