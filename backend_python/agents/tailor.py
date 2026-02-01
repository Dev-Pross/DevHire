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
from google import genai
from google.genai import types
from google.api_core import exceptions as g_exc
from config import GOOGLE_API, GROQ_API
from groq import Groq


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

# ╭── Gemini setup ───────────────────────────────────────────────╮
if not GOOGLE_API:
    raise ValueError("Set GOOGLE_API env var")
client = genai.Client(api_key=GOOGLE_API)
model_3 = "gemini-3-flash-preview"
model_2 = 'gemini-2.5-flash-lite' # gemini-2.5-flash-lite gemini-2.5-flash-preview-09-2025
model_1 = 'gemini-2.5-flash'
model_4 = 'gemini-robotics-er-1.5-preview'
# Ordered fallback list for retries
MODELS = [model_1, model_2, model_3, model_4]
# client = Groq(
#     api_key=GROQ_API,
# )
# model="groq/compound"

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
_SAMPLE0 = r"""
\documentclass[letterpaper,10pt]{article}
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage{fontawesome5} 
\usepackage[english]{babel}
\usepackage{tabularx}
\input{glyphtounicode}

% --- MARGINS & SPACING ---
\pagestyle{fancy}
\fancyhf{} 
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Optimized margins for 1-page fit
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1.0in}
\addtolength{\topmargin}{-0.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% --- SECTION FORMATTING ---
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large\bfseries
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% --- CUSTOM COMMANDS ---
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small\textbf{#1} & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-1pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
%  RESUME STARTS HERE
%-------------------------------------------
\begin{document}

%----------HEADER----------
\begin{center}
    {\Huge \bfseries Budumuru Srinivas Sai Saran Teja} \\ \vspace{3pt}
    {\Large \bfseries Backend Engineer \& GenAI Specialist} \\ \vspace{5pt}
    
    \small
    \faMapMarker* Visakhapatnam, India \ $|$ \ 
    \faPhone* +91 7993027519 \ $|$ \ 
    \faEnvelope \ \href{mailto:tejabudumuru3@gmail.com}{tejabudumuru3@gmail.com} \\ \vspace{4pt}
    
    \faLinkedin \ \href{https://www.linkedin.com/in/srinivas-sai-saran-teja-budumuru-15123a292/}{Linkedin} \ $|$ \ 
    \faGithub \ \href{https://github.com/TejaBudumuru3}{Github} \ $|$ \ 
    \faGlobe \ \href{https://teja-budumuru.vercel.app}{Portfolio}
\end{center}

%-----------PROFESSIONAL SUMMARY-----------
\section{Professional Summary}
Full-Stack AI Engineer capable of delivering end-to-end SaaS solutions. Proven ability to architect complex workflow engines (DAGs) and AI-powered platforms using the \textbf{MERN Stack} and \textbf{FastAPI}. Skilled in modern Cloud DevOps (\textbf{AWS/CI/CD}) and API design. Passionate about leveraging Large Language Models (LLMs) to solve complex business problems through intelligent, human-in-the-loop automation.

%-----------TECHNICAL SKILLS (Fixed & Complete)-----------
\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     \textbf{Languages}{: Python, JavaScript (ES6+), TypeScript, SQL, Java} \\
     \textbf{Backend \& AI}{: FastAPI, Node.js, Express.js, Microservices, Gemini API, Kafka, WebSockets, Webhook}
     \\
     \textbf{Frontend}{: React.js, Next.js, Tailwindcss, Bootstrap Css, HTML, CSS}
     \textbf{Database \& Infra}{: Supabase(PostgreSQL), MongoDB, Docker, AWS (EC2), CI/CD (GitHub Actions), Prisma ORM} \\
     \textbf{Tools \& Traits}{: Playwright, Redux, Postman, Git, Agile, Teamwork, Problem Solving}
    }}
 \end{itemize}

%-----------PROJECTS-----------
\section{Key Projects}
\resumeSubHeadingListStart

    % PROJECT 1: BuildFlow (N8N Clone)
    \resumeProjectHeading
    {\textbf{BuildFlow} $|$ \emph{Workflow Automation Engine}}
    {\href{https://github.com/Dev-Pross/BuildFlow}{Github}}
    \resumeItemListStart
        \resumeItem{\textbf{Spearheaded} the architecture of a low-code platform capable of executing \textbf{Directed Acyclic Graphs (DAGs)}, targeting sub-200ms latency per node.}
        \resumeItem{\textbf{Orchestrated} a distributed task processing system using \textbf{TypeScript} and \textbf{Kafka}, enabling asynchronous execution of concurrent workflows.}
        \resumeItem{\textbf{Formulated} a resilient state management module to handle execution context, mitigating workflow failures by \textbf{40\%} via automated error propagation.}
    \resumeItemListEnd

    % PROJECT 2: HireHawk
    \resumeProjectHeading
    {\textbf{HireHawk} $|$ \emph{AI Job Automation Agent}}
    {\href{https://dev-hire-znlr.vercel.app/}{Live Link}}
    \resumeItemListStart
        \resumeItem{\textbf{Devised} an AI Agent that curtails manual job application time by \textbf{80\%} using a "Human-in-the-Loop" architecture with \textbf{Playwright}.}
        \resumeItem{\textbf{Embedded} a \textbf{Context-Aware Resume Engine} that parses JDs and user data to dynamically synthesize tailored resumes using \textbf{Gemini API}.}
        \resumeItem{\textbf{Engineered} a high-volume batch processing pipeline capable of sustaining \textbf{10+ sequential applications} per session without IP throttling.}
    \resumeItemListEnd

    % PROJECT 3: Ainfinity
    \resumeProjectHeading
    {\textbf{Ainfinity} $|$ \emph{Generative AI Content SaaS}}
    {\href{https://post-generator-iota.vercel.app/}{Live Link}}
    \resumeItemListStart
        \resumeItem{\textbf{Constructed} a full-stack content generation platform using the \textbf{MERN Stack}, accelerating RESTful API response times to under \textbf{300ms}.}
        \resumeItem{\textbf{Fortified} secure session management using \textbf{HTTP-Only Cookies}, eliminating potential XSS and CSRF vulnerabilities.}
        \resumeItem{\textbf{Synchronized} global application state using \textbf{Redux Toolkit}, ensuring seamless data consistency across the frontend.}
    \resumeItemListEnd

\resumeSubHeadingListEnd

%-----------PROFESSIONAL EXPERIENCE-----------
\section{Professional Experience}
\resumeSubHeadingListStart

    \resumeSubheading
      {Backend API Engineer}{Remote}
      {Freelance Project: Resume Tailoring \& Portfolio Engine}{Nov 2025 -- Present}
      \resumeItemListStart
        \resumeItem{\textbf{Tailored} a production-ready API for generating ATS-friendly resumes, optimizing dynamic templates to reduce document generation latency by \textbf{40\%}.}
        \resumeItem{\textbf{Unified} data ingestion pipelines by creating polymorphic endpoints that process both raw JSON and PDF inputs.}
        \resumeItem{\textbf{Provisioned} production infrastructure on \textbf{AWS EC2} using Docker, ensuring \textbf{reliable 24/7 system availability} for client operations.}
      \resumeItemListEnd

\resumeSubHeadingListEnd

%-----------EDUCATION-----------
\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {MVGR College of Engineering (A)}{Vizianagaram}
      {B.Tech in Computer Science and Engineering;}{May 2025}
    \resumeSubheading
      {Government Polytechnic College}{Anakapalle}
      {Diploma in Computer Engineering; }{June 2022}
  \resumeSubHeadingListEnd

%-----------CERTIFICATIONS-----------
\section{Certifications}
\resumeSubHeadingListStart
    \resumeItem{\textbf{Oracle Certified Generative AI Professional (2025)} -- \href{https://catalog-education.oracle.com/ords/certview/sharebadge?id=BD6B7CF412F7B7B177182CB5A13B29CE3218255114ABB2C19070B7B5A512E48F}{[Verify Badge]}}
    \resumeItem{\textbf{Oracle Cloud Infrastructure Foundations Associate} -- \href{https://catalog-education.oracle.com/ords/certview/sharebadge?id=1DCE05167148ED0D0575B553F7110B6CACC6BFBA54E628910002B76EBE582144}{[Verify Badge]}}
\resumeSubHeadingListEnd

\end{document}
    """

_SAMPLE1 = r"""
\documentclass[a4paper,10pt]{article}
% FIX 1: Aggressive margins to maximize space (0.6cm)
\usepackage[left=0.6cm,top=0.6cm,right=0.6cm,bottom=0.6cm,nohead,nofoot]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{mathpazo} % Palatino Font
\usepackage{xcolor}
\usepackage{fontawesome5}
\usepackage{enumitem}
\usepackage{calc}
\usepackage{hyperref}

% --- COLORS ---
\definecolor{mainred}{RGB}{185, 0, 0}
\definecolor{headergray}{RGB}{60, 60, 60}

% --- GLOBAL SPACING ---
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\raggedright

% --- COMMANDS ---

% Compact Section Header
\newcommand{\resumesection}[1]{
    \vspace{8pt} % Reduced from 12pt
    {\large \textsc{\textbf{#1}}} \\[-3pt]
    {\color{mainred}\rule{2cm}{2pt}}
    \vspace{4pt} % Reduced from 8pt
}

% Compact Skill Bar
\newcommand{\skill}[3]{
    \noindent
    \begin{tabular*}{\linewidth}{@{}l@{\extracolsep{\fill}}r@{}}
        \textbf{\small #1} & {\footnotesize #2} \\
    \end{tabular*}%
    \\[-3pt]
    {\color{mainred}\rule{#3\linewidth}{3pt}}
    \vspace{3pt}
}

% Compact Job Header
\newcommand{\jobheader}[3]{
    \noindent
    {\textbf{#1}} \\
    {\small \textit{#2}} \hfill 
    \colorbox{mainred}{\makebox[2.5cm][c]{\color{white}\bfseries\footnotesize #3}}
    \vspace{2pt}
}

% Contact Item
\newcommand{\contactitem}[2]{
    \vspace{2pt}
    \noindent
    \makebox[0.4cm][c]{\color{mainred}\faIcon{#1}} \hspace{2pt} \small #2 
}

\begin{document}

% ====================================================================
% LEFT COLUMN (Sidebar) - 30% width
% ====================================================================
\begin{minipage}[t]{0.30\textwidth}
    \vspace{0pt} 

    % --- SKILLS ---
    \resumesection{SKILLS}
    
    \skill{Python / FastAPI}{Advanced}{0.95}
    \skill{React / TS}{Advanced}{0.90}
    \skill{Next.js}{Advanced}{0.85}
    \skill{Git / GitHub}{Advanced}{0.90}
    \skill{PostgreSQL}{Intermediate}{0.75}
    \skill{REST APIs / JWT}{Advanced}{0.80}
    \skill{Gen AI / LLMs}{Intermediate}{0.70}
    \skill{Docker}{Intermediate}{0.65}
    \skill{Playwright}{Intermediate}{0.65}

    \vspace{2cm} % Flexible Spacer

    % --- CONTACT ---
    \resumesection{CONTACT}
    
    \contactitem{map-marker-alt}{Visakhapatnam, India}
    \contactitem{phone-alt}{+91 7993027519}
    \contactitem{envelope}{tejabudumuru3\\@gmail.com}
    \contactitem{linkedin-in}{\href{https://linkedin.com/in/teja-budumuru-15123a292}{LinkedIn Profile}}
    \contactitem{github}{\href{https://github.com/TejaBudumuru3}{GitHub Profile}}
    \contactitem{globe}{\href{https://teja-budumuru.vercel.app}{Portfolio Link}}

\end{minipage}%
\hfill 
% ====================================================================
% RIGHT COLUMN (Main) - 66% width
% ====================================================================
\begin{minipage}[t]{0.66\textwidth}
    \vspace{0pt} 

    % --- HEADER BOX ---
    \noindent
    \colorbox{headergray}{
        \begin{minipage}[c][3.0cm][c]{\dimexpr\linewidth-2\fboxsep}
            \centering
            \color{white}
            {\huge \textsc{BUDUMURU SRINIVAS}} \\ [3pt]
            {\huge \textsc{SAI SARAN TEJA}} \\ [6pt]
            {\rule{0.5\linewidth}{0.5pt}} \\ [6pt]
            {\large AI Full-Stack Engineer}
        \end{minipage}
    }
    
    \vspace{8pt}

    % --- PROFILE ---
    \resumesection{PROFILE}
    \small % Slightly smaller text for body
    Highly motivated AI Full-Stack Engineer with a strong portfolio demonstrating end-to-end ownership in building AI-driven web applications. Proficient in \textbf{React/TypeScript} for robust frontends and \textbf{Python/FastAPI} for scalable backend APIs. Experienced in designing RESTful APIs, managing PostgreSQL databases, and integrating LLMs for agentic AI workflows. Certified in Oracle Cloud Infrastructure Generative AI.

    % --- EXPERIENCE / PROJECTS ---
    \resumesection{WORK EXPERIENCE}

    % Project 1
    \jobheader{HireHawk - Auto-Apply Platform}{Next.js, FastAPI, Docker}{Sep '24 - Present}
    \begin{itemize}[leftmargin=*, nosep, topsep=1pt, itemsep=1pt] \small
        \item Architected an end-to-end platform using \textbf{Next.js} (frontend) and \textbf{FastAPI} (backend) for job automation.
        \item Developed a \textbf{Playwright}-driven engine for dynamic form filling, reducing manual effort by \textbf{80\%}.
        \item Implemented robust RESTful APIs with \textbf{JWT} authentication and PostgreSQL data models.
        \item Containerized services with \textbf{Docker} and established CI/CD for Vercel deployments.
        \item Optimized database models and applied security hardening (CORS, Rate Limiting).
    \end{itemize}
    \vspace{6pt}

    % Project 2
    \jobheader{Ainfinity - AI Content SaaS}{MERN Stack, LLM, Redux}{Jan '24 - Aug '24}
    \begin{itemize}[leftmargin=*, nosep, topsep=1pt, itemsep=1pt] \small
        \item Developed an AI-powered SaaS using \textbf{React.js} and \textbf{Node.js} for generating social media content.
        \item Integrated \textbf{LLM APIs} with configurable system prompts for structured, safe generation.
        \item Implemented secure JWT-based authentication with \textbf{RBAC} (Role-Based Access Control).
        \item Engineered reusable components and optimized API routes for performance and pagination.
    \end{itemize}

    % --- EDUCATION ---
    \resumesection{EDUCATION}
    
    \jobheader{B.Tech in Computer Science}{MVGR College of Engineering (A)}{2022 - 2025}
    \begin{itemize}[leftmargin=*, nosep] \small
        \item GPA: 7.48 / 10
    \end{itemize}
    \vspace{4pt}
    
    \jobheader{Diploma in Computer Engineering}{Government Polytechnic College}{2019 - 2022}
    \begin{itemize}[leftmargin=*, nosep] \small
        \item Grade: 82.09\%
    \end{itemize}

    % --- CERTIFICATIONS ---
    \resumesection{CERTIFICATIONS}
    \begin{itemize}[leftmargin=*, nosep, topsep=1pt] \small
        \item Oracle Cloud Infrastructure 2025 Certified Generative AI Professional
        \item Oracle Cloud Infrastructure 2025 Certified Generative AI Associate
        \item AI and Machine Learning – AICTE
    \end{itemize}

    % --- ACHIEVEMENTS ---
    \resumesection{ACHIEVEMENTS}
    \begin{itemize}[leftmargin=*, nosep, topsep=1pt] \small
        \item Finalist in Pega Systems Hackathon (Web Automation).
        \item Finalist in academic drawing competition (Design Sense).
    \end{itemize}

\end{minipage}

\end{document}
"""

_SAMPLE2 = r"""
\documentclass[12pt,a4paper,sans]{moderncv}

\moderncvstyle{classic}
\moderncvcolor{blue}
\usepackage[scale=0.75]{geometry}
\usepackage[utf8]{inputenc}

% --- FIX IS HERE ---
% {34} = Font Size
% {40} = Line Height (Reduced from 80 to 40)
% This allows auto-wrapping with tight padding.
\renewcommand*{\namefont}{\fontsize{34}{34}\mdseries\upshape\selectfont}

% --- PERSONAL DATA ---
% Put the full name here. LaTeX will automatically wrap it to the next line 
% when it hits the margin, and the {40} above will keep the lines close.
\firstname{BUDUMURU SRINIVAS SAI SARAN TEJA\\[5pt}
\title{Full Stack Developer \& AI Specialist} 
\address{Visakhapatnam}{Andhra Pradesh}
\mobile{+91 9876543210}
\email{your.email@example.com}
\homepage{github.com/yourusername} 
\social[linkedin]{linkedin.com/in/yourusername}

\begin{document}

\makecvtitle

% --- Education ---
\section{Education}
\cventry{2021--2025}{B.Tech Computer Science}{Andhra University}{Visakhapatnam}{}{Focused on Software Development and AI Integration.}

% --- Skills ---
% Using \cvitem ensures the category aligns neatly on the left
\section{Technical Skills}
\cvitem{Languages}{Python, TypeScript, JavaScript, SQL}
\cvitem{Frontend}{Next.js, React, Tailwind CSS, HTML5/CSS3}
\cvitem{Backend}{FastAPI, Node.js, Express, Microservices}
\cvitem{AI \& LLMs}{RAG Architecture, Context Embeddings, Gemini API, LangChain}
\cvitem{DevOps/Tools}{Docker, Git, N8N (Workflow Automation), Oracle Cloud (OCI)}

% --- Projects ---
% \cventry args: {Year}{Title}{Subtitle/Stack}{Location}{}{Description}
\section{Projects}

\cventry{Ongoing}{DevHire (HireHawk)}{AI Job Automation Platform}{}{}{
\begin{itemize}
    \item Developing an automated tool to streamline the job application process on platforms like LinkedIn.
    \item Features include AI resume parsing, auto-filling applications, and a real-time tracking dashboard.
    \item \textbf{Tech Stack:} Next.js, Python, Selenium/Playwright, AI Integration.
\end{itemize}
}

\vspace{5pt}

\cventry{2025}{Ainfinity}{AI Content Generation App}{}{}{
\begin{itemize}
    \item Designed a full-stack web application for generating creative marketing content and visuals.
    \item Created a high-conversion Hero section and integrated generative AI APIs.
    \item \textbf{Tech Stack:} Next.js, React, AI APIs.
\end{itemize}
}

\vspace{5pt}




% --- Certifications ---
\section{Certifications}
\cvlistitem{Oracle Cloud Infrastructure (OCI) Generative AI Professional}
\cvlistitem{Oracle Cloud Infrastructure (OCI) Associate}


% --- Languages ---
\section{Languages}
\cvlistitem{English} \title{fluent}
\cvlistitem{Telugu}

\end{document}
"""

_SAMPLE3 = r"""
    \documentclass[a4paper,12pt]{article}
\usepackage[left=1cm, top=1cm, right=1cm, bottom=1cm]{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{tabularx}
\usepackage{fontawesome5}

% --- COLORS ---
\definecolor{headerblue}{RGB}{0, 60, 120}
\definecolor{labelgrey}{RGB}{80, 80, 80}

% --- SETTINGS ---
\pagestyle{empty} % No page numbers
\setlength{\parindent}{0pt}
\setlength{\tabcolsep}{10pt} % Spacing between Date and Content columns

% --- CUSTOM COMMANDS ---

% 1. Section Heading (Uppercase, Bold, Blue, with Line)
\titleformat{\section}
{\Large\bfseries\color{headerblue}\uppercase}
{}
{0em}
{}[\titlerule]
\titlespacing{\section}{0pt}{12pt}{8pt}

% 2. Main Entry Command (The Grid)
% Usage: \gridentry{Left Label}{Title}{Right Label (e.g. Stack/Loc)}{Description}
\newcommand{\gridentry}[4]{
    \noindent
    \begin{tabularx}{\linewidth}{@{} r | X @{}} % The | creates a subtle vertical divider
        \begin{minipage}[t]{2.8cm}
            \raggedleft \small \bfseries \color{labelgrey} #1
        \end{minipage} 
        & 
        \begin{minipage}[t]{\linewidth}
            \textbf{\large #2} \hfill \textit{\small #3} \par
            \vspace{3pt}
            \small #4
        \end{minipage}
    \end{tabularx}
    \vspace{6pt}
}

% 3. Simple Skill Row
\newcommand{\skillrow}[2]{
    \noindent
    \begin{tabularx}{\linewidth}{@{} r | X @{}}
        \begin{minipage}[t]{2.8cm}
            \raggedleft \small \bfseries \color{labelgrey} #1
        \end{minipage} 
        & 
        \small #2
    \end{tabularx}
    \vspace{4pt}
}

% 4. Tighter Lists
\setlist[itemize]{leftmargin=*, nosep, topsep=2pt, itemsep=2pt}

\begin{document}

% --- HEADER ---
\begin{center}
    {\Huge \textbf{BUDUMURU SRINIVAS SAI SARAN TEJA \\[5pt]}}  \vspace{16pt}
    {\Large \color{headerblue} Full Stack Developer \& AI Specialist} \\ \vspace{8pt}
    
    \small
    \faMapMarker* Visakhapatnam, India \quad $|$ \quad
    \faPhone* +91 9876543210 \quad $|$ \quad
    \faEnvelope \ \href{mailto:your.email@example.com}{your.email@example.com} \\ \vspace{3pt}
    \faLinkedin \ \href{https://linkedin.com/in/yourusername}{linkedin.com/in/yourusername} \quad $|$ \quad
    \faGithub \ \href{https://github.com/yourusername}{github.com/yourusername}
\end{center}

\vspace{5pt}

\section{Professional Summary}
\begin{itemize}
        \text{  Full-Stack Software Engineer focused on building \textbf{AI-driven web products} using the \textbf{MERN stack}, \textbf{Python (FastAPI/Flask)}, and modern frontend frameworks like \textbf{React.js/Next.js}. 
    Led end-to-end development of projects such as \textbf{HireHawk} (intelligent job-application platform) and \textbf{Ainfinity/Post Generator} (Generative AI content platforms), combining solid API design, scalable data models, and responsive UIs to solve real user problems. 
    Certified in \textbf{Oracle Cloud Infrastructure Generative AI}, with a strong interest in applying LLMs and workflow orchestration to create next-generation SaaS tools for the Indian market that are practical, reliable, and ready for production. 
    Keen on roles where full-stack engineering, product thinking, and applied AI intersect to deliver measurable business impact rather than purely academic prototypes. }
\end{itemize}
% --- SKILLS ---
\section{Technical Skills}
% The vertical bar | aligns perfectly across the whole document
\skillrow{Languages}{Python, TypeScript, JavaScript, SQL, Java}
\skillrow{Frameworks}{Next.js, React.js, FastAPI, Node.js, Express.js}
\skillrow{AI \& LLM}{RAG Architecture, LangChain, Context Embeddings, Gemini API}
\skillrow{DevOps}{Docker, Git, GitHub Actions, Vercel, OCI (Oracle Cloud)}

% --- PROJECTS ---
\section{Key Projects}

\gridentry{Ongoing}{DevHire (HireHawk)}{Next.js, Python, Playwright}{
    An intelligent job automation platform for LinkedIn.
    \begin{itemize}
        \item Engineered AI resume parsing to auto-fill job applications using \textbf{Selenium} and \textbf{Playwright}.
        \item Built a reactive dashboard with \textbf{Next.js} and Redux for real-time application tracking.
        \item Integrated secure authentication and role-based access control.
    \end{itemize}
}

\gridentry{2025}{Ainfinity}{MERN Stack, GenAI}{
    A SaaS platform for automated content generation.
    \begin{itemize}
        \item Developed a scalable backend using \textbf{Node.js} and Microservices architecture.
        \item Integrated Generative AI APIs to create high-conversion marketing copy and visuals.
        \item Designed a responsive, high-performance UI using React and Tailwind CSS.
    \end{itemize}
}

\gridentry{2025}{Second Brain}{Python, Vector DB, RAG}{
    AI-powered personal knowledge base.
    \begin{itemize}
        \item Implemented Retrieval-Augmented Generation (RAG) to chat with personal notes.
        \item Optimized context embeddings for accurate information retrieval from Vector DB.
    \end{itemize}
}

% --- EDUCATION ---
\section{Education}

\gridentry{2021 -- 2025}{B.Tech Computer Science}{Andhra University}{
    \textit{Visakhapatnam, Andhra Pradesh} \\
    Specialized in Software Engineering and Artificial Intelligence.
}

\gridentry{2019 -- 2021}{Diploma in Computer Eng.}{Govt Polytechnic}{
    \textit{Visakhapatnam, Andhra Pradesh} \\
    Graduated with Distinction.
}

% --- CERTIFICATIONS ---
\section{Certifications}

\gridentry{2025}{OCI Generative AI Professional}{Oracle Cloud}{
    Validated expertise in building, training, and deploying LLMs on Oracle Cloud Infrastructure.
}

\gridentry{2025}{OCI Associate}{Oracle Cloud}{
    Core understanding of cloud architecture, networking, and security.
}

% --- Languages ---

\section{Languages}

\gridentry{Fluent}{English}{}{}
\\[2pt]
\gridentry{Native}{Telugu}{}{}
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

2.  **Tailor with Precision and Honesty**: You will strategically rewrite specific sections of the resume to align with the job description. However, you must never invent skills or experiences the candidate does not possess. Your goal is to highlight existing qualifications, not to fabricate new ones. Don't use repeated verbs, use fancy verbs and make sure grammatical mistake free resume with short Professional Summary for single page resume(SPR) to fit all content in one page it self only for FRESHER /(NO PROFESSIONAL EXPERIENCED CANDIDATES)
    * **Rationale**: Honesty is paramount. While the goal is to pass ATS scans, the resume must be a truthful representation of the candidate for the human hiring manager who will read it next.

3.  **Reconstruct with Flawless Code**: The final output must be a syntactically perfect LaTeX document formatted according to the provided template.
    * **Rationale**: The end product is code. It must compile without errors. All data, especially reconstructed hyperlinks, must be correctly formatted within the LaTeX structure.

4.  **Output**: You must return error free LaTex code(**MANDATORY)
---
## Generation Algorithm: EXECUTE EXACTLY

**Purpose**: To provide a sequential, step-by-step program. Following this algorithm precisely prevents errors and ensures all requirements are met in the correct order.

**Step 1: Parse and Structure the Raw PDF Text**
- **Task**: Read the `<EXTRACTED_PDF_TEXT>`. Intelligently identify and group the text into logical sections: Name, Contact Info, Professional Summary, Education, Technical Skills, Projects, Work Experience (if any), Certifications, Achievements, and Languages.
- **Rationale**: This creates a clean, structured "database" of the candidate's information.
- **CRITICAL LAYOUT CHECK**: Analyze the `<LATEX_TEMPLATE>`. If it is a **single-page, 2-column layout**, you MUST enforce a strict content limit. The final output **MUST** fit perfectly on one page. You are prohibited from generating content that spills onto a second page for these templates. (**MANDATORY**)
- **CRITICAL LAYOUT CHECK**: For every `<LATEX_TEMPLATE>`, you must follow the alignments like: Profile, Contact, Skills, Projects, Titles and even spacing as it is take care about content that will be generated as per ATS and page limits (Max. 2-columned format resume) and strict alignments as per the `<LATEX_TEMPLATE>`. (**MANDATOTY**) 

**Step 2: Analyze the Job Description and Extract Keywords**
- **Task**: Read the `<JOB_DESCRIPTION>` and identify the top 5-10 most important keywords. These are specific technologies, methodologies, or responsibilities.
- **Rationale**: To tailor effectively, you must know the target. This keyword list is your "checklist" for Step 5.

**Step 3: Reconstruct Static Sections and Hyperlinks**
- **Task**: Build the sections that do not need tailoring (Education, Certifications, Achievements, Languages). Reconstruct contact info and hyperlinks.
    - **LinkedIn**: `\href{https://linkedin.com/in/user}{LinkedIn}`
    - **GitHub**: `\href{https://github.com/user}{GitHub}`
    - **Projects**: If parsed text contains a URL, reconstruct it using `\href`.
- **Rationale**: Explicitly reconstructing URLs is critical as they are often mangled during extraction.

**Step 4: Analyze Experience Level**
- **Task**: Determine if "Work Experience" exists. "Projects" alone = "Fresher". Valid work history = "Experienced".
- **Rationale**: Critical for choosing the section order.

**Step 5: Define Section Order**
- **Task**: Select the order based on Step 4.
    - **Fresher**: Heading, Summary, Education, Skills, Projects, Certifications, Achievements, Languages.
    - **Experienced**: Heading, Summary, Skills, Work Experience, Projects, Education, Certifications.
- **Rationale**: Highlights the most important information first.

**Step 6: Execute ATS-Friendly Content Tailoring (Layout Aware)**
- **Task**: Rewrite dynamic sections using keywords from Step 2.
    - 1. **Summary**: Target the JD directly.
    - 2. **Skills**: Mirror JD keywords.
    - 3. **Projects/Experience**: Rewrite bullets to showcase accomplishments.
- **CONSTRAINT**: If Step 1 identified a **Single-Page Template**, you must prioritize **CONCISENESS**. Limit bullet points to 3-4 per project. Remove "fluff" words. Ensure the generated text volume will mathematically fit into the template's available space.
- **Rationale**: Core creative step. Concise writing prevents layout overflow.

**Step 7: Assemble Final LaTeX Document**
- **Task**: Construct the final LaTeX file using the `<LATEX_TEMPLATE>`. Populate it with the tailored content.
- **Rationale**: Final assembly. Ensure no valid content is left out, but respect page boundaries.

---
## Output Requirements

**Purpose**: To define the strict API contract for your response.

1.  **Delimiter**: Start each job's output with `=== JOB {number} ===`.
2.  **No-Change Condition**: If the resume is already a perfect match, the block must contain only `NO_CHANGES_NEEDED`.
3.  **LaTeX Output**: Otherwise, the block must contain the complete, valid LaTeX code, starting with `\documentclass`.
"""

def build_prompt(original_resume: str, jobs: List[str]) -> str:
    global _TEMPLATE
    if _TEMPLATE == 0:
        selected_tempalate = _SAMPLE0
    elif _TEMPLATE == 1:
        selected_tempalate = _SAMPLE1
    elif _TEMPLATE == 2:
        selected_tempalate = _SAMPLE2
    elif _TEMPLATE == 3:
        selected_tempalate = _SAMPLE3
    else:
        selected_tempalate = _SAMPLE0
    logging.warning(f"{_TEMPLATE} -  template")
    # Start with the core instructions and the template
    prompt_parts = [
        SYSTEM_INSTRUCTIONS,
        "## LaTeX Template for Formatting (Style Reference Only)",
        "<LATEX_TEMPLATE>",
        selected_tempalate,
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
                config=types.GenerateContentConfig(temperature=0.2)
            ).text

            # ADD THIS LINE TO SAVE GEMINI RESPONSE:
            # Path(f"gemini_debug_{int(time.time())}.txt").write_text(txt, encoding="utf-8")

            # log.debug("Gemini preview: %s", txt.choices[0].message.content[:300].replace("\n", " ↩ "))
            # return txt.choices[0].message.content
            log.debug("Gemini preview: %s", res[:300].replace("\n", " ↩ "))
            # if any(code in res for code in ("404", "429", "503")):
            #     choose_model = model_2
            #     log.warning("Model switched to fallback due to error: model changed")
            return res
        except Exception as e:
            # log.error("Gemini error: %s", str(e))
            # Correctly detect specific HTTP/Status codes in the error text
            if any(code in str(e) for code in ("404", "429", "503")):
                # Move to next fallback model if available
                prev_model = choose_model
                if model_idx < len(MODELS) - 1:
                    model_idx += 1
                    choose_model = MODELS[model_idx]
                    log.warning("Switching model due to error (%s) → %s", e, choose_model)
                else:
                    log.warning("Already on last fallback model (%s); will retry", choose_model)
            else:
                log.error("Gemini error: %s", str(e))
            # Wait, then retry next attempt (do not break)
            time.sleep(delay)
            continue
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
        try:
            original_txt = extract_resume_text(resume_url)
        except Exception as e:
            log.error("Failed to extract resume text: %s", str(e))
            raise
    else:
        original_txt = user_data
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
            pdf = b""
            if not blk or _norm(blk) == "NO_CHANGES_NEEDED":
                if original_pdf: 
                    pdf = original_pdf
                    log.debug("Job %d: no changes", i)
            else:
                tex = tex_from_block(blk)
                pdf = compile_tex(tex) if tex else None
                if not pdf:
                    if original_pdf:
                        pdf = original_pdf
                    else:
                        log.warning("Failed to generate PDF")
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
