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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t:
        t.write(r.content)
        p = t.name
    try:
        doc = fitz.open(p)
        txt = "".join(pg.get_text() for pg in doc)
        doc.close()
        return txt
    finally:
        os.remove(p)

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
    if "word" in ct or url.lower().endswith(".docx"):
        return _docx_to_txt(r)
    raise ValueError("Unsupported resume format")
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Prompt builder ─────────────────────────────────────────────╮
_SAMPLE = r"""
\documentclass[a4paper,10pt]{article}

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

RULES = r"""
For each job description:

- For every provided job description:

    - If the current résumé fully matches the job requirements, respond with only the text: NO_CHANGES_NEEDED.

    - Explain projects and all stuff in detail, if it matches the job description and resume more professional align and professional format.

    - Use only Original resume data like name, phone, email all stuff take only from original resume, from sample resume take only layout, margins, spacing stuff

    - Otherwise, respond with a COMPLETE LaTeX résumé, starting with \documentclass and ending with \end{document}. Do not include any explanation or markdown, only the valid LaTeX code.

    - The code must never contain any LaTeX syntax errors (this is mandatory).

- Layout and Spacing Rules:

    - Ensure all sections (Professional Summary, Skills, Education, Projects, Certifications, Achievements, Languages, etc.) have clear and consistent vertical spacing above and below each heading and item for readability.

    - DO NOT squeeze sections too tightly together or eliminate vertical spacing between sections to force all content onto a single page.

    - Maintain a minimum of 0.5cm space (or a similar appropriate value) between major sections. Use LaTeX vertical spacing commands like \vspace{8pt} or appropriate list spacing parameters.

    - The bottom of every page must have visible white space: ensure there is consistent buffer space between the last line of content and the bottom page edge (the bottom margin) so the résumé does not appear congested at the bottom.

    - Use a minimum bottom margin of 2.5 cm, either by setting document margins (e.g., using the geometry package) or ensuring \textheight is not maximized (mandatory).

    - Do NOT artificially fill the page with empty space to get a full page—let pages break naturally. If there is little content for the second page, allow it to remain mostly blank on purpose for professional appearance.

    - Do NOT force content onto the next page by adding excessive manual spacing or blank lines.

    - All LaTeX code must ensure balanced visuals: if a page has little content, allow the natural blank space, but never place a section header near the absolute bottom of a page by itself (avoid 'widow' or 'orphan' lines).

- Job Numbering:

    -Every résumé code must start with the job number, e.g., '=== JOB 1 ===' (plain text, not commented or styled).
"""

def build_prompt(original: str, jobs: List[str]) -> str:
    out = f"ORIGINAL RESUME TEXT:\n{original}\n\n{RULES}\n\n"
    out += f"Sample format Gemini must follow:\n{_SAMPLE}\n\n"
    for i, jd in enumerate(jobs, 1):
        out += f"=== JOB {i} ===\n{jd}\n"
    return out
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
