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
from docx import Document
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
model = genai.GenerativeModel("gemini-2.5-flash-lite")
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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as t:
        t.write(r.content)
        p = t.name
    try:
        d = Document(p)
        return "\n".join(par.text for par in d.paragraphs)
    finally:
        os.remove(p)

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
\usepackage{marvosym}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-0.6in}
\addtolength{\textheight}{1.5in}

% Formatting for section titles
\titleformat{\section}{%
  \scshape\raggedright\large
}{}{0em}{}[\titlerule]

\newcommand{\resumeItem}[1]{\item\small{{#1 \vspace{-2pt}}}}
\newcommand{\resumeSubheading}[4]{\vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      {\bfseries #1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-5pt}
}
\newcommand{\resumeProjectHeading}[2]{\item
  \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
    {\bfseries #1} & \textit{#2} \\
  \end{tabular*}\vspace{-6pt}
}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-10pt}}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}\vspace{-15pt}}
% New command for Languages section to reduce downward shift
\newcommand{\resumeSubHeadingListEndNoSpace}{\end{itemize}\vspace{-5pt}}

\begin{document}

%----------HEADING----------
\begin{center}
    {\Huge \bfseries Budumuru Srinivas Sai Saran Teja} \\ \vspace{1pt}
    Visakhapatnam, India $|$ +91 7993027519 $|$ \href{mailto:tejabudumuru3@gmail.com}{tejabudumuru3@gmail.com} \\
    \href{https://linkedin.com/in/teja-budumuru-15123a292}{LinkedIn} $|$ 
    \href{https://github.com/TejaBudumuru3}{GitHub}
\end{center}

%-----------PROFESSIONAL SUMMARY-----------
\section{Professional Summary}
\resumeSubHeadingListStart
\resumeItem{
Enthusiastic and detail-oriented \textbf{Software Developer (Fresher)} with strong foundations in \textbf{OOPs, data structures, DBMS}, and hands-on experience building fullstack applications using \textbf{JavaScript, React.js, Node.js, Express.js, and MongoDB}. Adept at writing clean, efficient code, collaborating with cross-functional teams, and quickly learning new technologies in fast-paced, remote-first environments.
}
\resumeSubHeadingListEnd

%-----------TECHNICAL SKILLS-----------
\section{Technical Skills}
\resumeItemListStart
  \resumeItem{\textbf{Programming Languages:} JavaScript (ES6+), Python, Java, SQL}
  \resumeItem{\textbf{Frontend:} React.js, Redux, HTML5, CSS3}
  \resumeItem{\textbf{Backend:} Node.js, Express.js, REST APIs}
  \resumeItem{\textbf{Databases:} MongoDB, MySQL}
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
    {Ainfity – AI-Powered Post Generator for Content Creators}{{\href{https://post-generator-iota.vercel.app/}{https://post-generator-iota.vercel.app/}}}
    \resumeItemListStart
      \resumeItem{Built a MERN stack application enabling AI-driven content generation, supporting both text and image creation for social media posts.}
      \resumeItem{Developed scalable RESTful APIs using Express.js and MongoDB with clean, modular backend architecture.}
      \resumeItem{Designed a responsive frontend interface with React.js, enhancing user experience across devices.}
      \resumeItem{Implemented secure authentication via JWT and optimized performance for smooth content creation workflows.}
    \resumeItemListEnd


\resumeProjectHeading
    {Faculty Performance Monitor}{}
    \resumeItemListStart
      \resumeItem{Developed a Java-based web portal using JSP and MySQL for role-based workload tracking and reporting.}
      \resumeItem{Optimized SQL queries for performance and applied MVC architecture for clean design.}
    \resumeItemListEnd

\resumeProjectHeading
    {Employee Management System}{}
    \resumeItemListStart
      \resumeItem{Built a payroll automation tool in Python with Tkinter GUI and MySQL, reducing manual processing time.}
      \resumeItem{Ensured data integrity with robust validation and exception handling.}
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
  \resumeItem{Participated in Pega Systems Hackathon demonstrating problem-solving and collaboration.}
  \resumeItem{Recognized for artistic talent in Drawing Competition (early academic years).}
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
- If the current résumé already matches the job, respond with ONLY the text NO_CHANGES_NEEDED.
- Otherwise respond with a COMPLETE LaTeX résumé that starts with \documentclass and ends with \end{document}.
- Do not include any explanation or markdown – ONLY the LaTeX code.
- Do not make any syntax errors in the LaTeX code (this is mandatory).
- Make sure every resume code is starts with job numbering like this '=== JOB 1 ==='.
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
            Path(f"gemini_debug_{int(time.time())}.txt").write_text(txt, encoding="utf-8")

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
