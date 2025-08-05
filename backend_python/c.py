#!/usr/bin/env python3
"""
Batch résumé-tailoring pipeline – COLORED-DEBUG v3
──────────────────────────────────────────────────
-  Colour-coded logs.
-  Single download of the original PDF.
-  Robust prompt → Gemini now returns real LaTeX.
-  Tolerant parsing + graceful fallback.
"""

import base64, json, logging, os, re, tempfile, time
from pathlib import Path
from typing import List, Dict, Any
import re
import fitz, requests                       # PyMuPDF / HTTP
from docx import Document
import google.generativeai as genai
from google.api_core import exceptions as g_exc
from config import GOOGLE_API

# ╭─────────────────────────  COLOUR LOG  ─────────────────────────╮
class _C: R="\33[31m"; G="\33[32m"; Y="\33[33m"; C="\33[36m"; M="\33[35m"; Z="\33[0m"
_PALETTE = {"DEBUG":_C.C,"INFO":_C.G,"WARNING":_C.Y,"ERROR":_C.R,"CRITICAL":_C.M}
class _Fmt(logging.Formatter):
    def format(self, rec):
        rec.levelname=f"{_PALETTE.get(rec.levelname,_C.Z)}{rec.levelname}{_C.Z}"
        return super().format(rec)
hlr=logging.StreamHandler();hlr.setFormatter(_Fmt("%(asctime)s | %(levelname)s | %(message)s"))
logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO").upper(),handlers=[hlr])
log=logging.getLogger("tailor")
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Gemini setup ───────────────────────────────────────────────╮
if not GOOGLE_API: raise ValueError("Set GOOGLE_API env var")
genai.configure(api_key=GOOGLE_API)
model = genai.GenerativeModel("gemini-2.5-flash")
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Resume-text helpers ────────────────────────────────────────╮
def _pdf_to_txt(r):
    with tempfile.NamedTemporaryFile(delete=False,suffix=".pdf") as t: t.write(r.content); p=t.name
    try:
        doc=fitz.open(p); txt="".join(pg.get_text() for pg in doc); doc.close(); return txt
    finally: os.remove(p)

def _docx_to_txt(r):
    with tempfile.NamedTemporaryFile(delete=False,suffix=".docx") as t: t.write(r.content); p=t.name
    try:
        d=Document(p); return "\n".join(par.text for par in d.paragraphs)
    finally: os.remove(p)

def extract_resume_text(url:str)->str:
    r=requests.get(url,timeout=60); r.raise_for_status()
    ct=r.headers.get("Content-Type","").lower()
    if "pdf" in ct or url.lower().endswith(".pdf"):  return _pdf_to_txt(r)
    if "word" in ct or url.lower().endswith(".docx"): return _docx_to_txt(r)
    raise ValueError("Unsupported resume format")
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Prompt builder ─────────────────────────────────────────────╮
_SAMPLE = r"""\documentclass[11pt]{article}
\begin{document}
...
\end{document}"""

RULES = r"""
For each job description:
- If the current résumé already matches the job, respond with ONLY the text NO_CHANGES_NEEDED.
- Otherwise respond with a COMPLETE LaTeX résumé that starts with \documentclass and ends with \end{document}.
- Do not include any explanation or markdown – ONLY the LaTeX code.
- Do not make any syntax errors in the LaTex code (this is mandatory).
- Make sure every resume code is starts with job numbering like this '=== JOB 1 ==='.
"""

def build_prompt(original:str,jobs:List[str])->str:
    out=f"ORIGINAL RESUME TEXT:\n{original}\n\n{RULES}\n\n"
    out+=f"Sample format Gemini must follow:\n{_SAMPLE}\n\n"
    for i,jd in enumerate(jobs,1): out+=f"=== JOB {i} ===\n{jd}\n"
    return out
# ╰───────────────────────────────────────────────────────────────╯

# ╭── Gemini call ------------------------------------------------╮
def ask_gemini(orig:str,jobs:List[str])->str:
    prompt=build_prompt(orig,jobs)
    for attempt,delay in zip(range(1,4),(0,20,40)):
        try:
            log.info("Gemini attempt %d/3",attempt)
            txt=model.generate_content(prompt).text.strip()
            
            # ADD THIS LINE TO SAVE GEMINI RESPONSE:
            Path(f"gemini_debug_{int(time.time())}.txt").write_text(txt, encoding="utf-8")
            
            log.debug("Gemini preview: %s", txt[:300].replace("\n"," ↩ "))
            return txt
        except g_exc.ResourceExhausted:
            log.warning("Rate-limited – sleep %ss",delay); time.sleep(delay)
    raise RuntimeError("Gemini failed 3×")


# ╰───────────────────────────────────────────────────────────────╯

# ╭── Parsing helpers ────────────────────────────────────────────╮
def _split(text:str,count:int)->List[str]:
    seg=re.split(r"===\s*JOB\s+(\d+)\s*===",text)
    blk={int(seg[i]):seg[i+1].strip() for i in range(1,len(seg),2) if i+1<len(seg)}
    return [blk.get(n,"") for n in range(1,count+1)]
def _norm(s:str)->str: return re.sub(r"\s+","",s).upper()
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
ENGINES=[("ytotech","https://latex.ytotech.com/builds/sync","orig"),
         ("latexonline","https://latexonline.cc/compile","orig"),
         ("api.online","https://api.latexonline.cc/compile","orig"),
         ("texlive","https://texlive.net/run","texlive"),
         ("codecogs","https://latex.codecogs.com/pdf.download","direct")]
def compile_tex(tex:str)->bytes|None:
    tex = soften_hboxes(tex)
    for name,url,m in ENGINES:
        try:
            log.info("Trying %s...", name)  # Show which endpoint we're trying
            if m=="orig":
                r=requests.post(url,files={"texfile":("main.tex",tex)},data={"command":"pdflatex"},timeout=120)
            elif m=="texlive":
                r=requests.post(url,files={"file":("m.tex",tex)},data={"format":"pdf","engine":"pdflatex"},timeout=120)
            else:
                r=requests.post(url,data=tex,headers={"Content-Type":"application/x-latex"},timeout=120)
            
            # Show HTTP status for all responses
            log.info("%s returned HTTP %d", name, r.status_code)
            
            if 200<=r.status_code<300 and r.content.startswith(b"%PDF"):
                log.info("✅ Compiled successfully via %s",name)
                return r.content
            else:
                # Show WHY it failed
                if not r.content.startswith(b"%PDF"):
                    log.warning("❌ %s: Not a valid PDF response", name)
                    log.warning("Response preview: %s", r.text[:200])  # Show first 200 chars
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


def tex_from_block(text:str)->str|None:
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
def process_batch(resume_url:str,jobs:List[Dict[str,str]])->List[Dict[str,Any]]:
    log.info("Processing %d jobs",len(jobs))
    original_pdf=requests.get(resume_url,timeout=60).content
    original_txt=extract_resume_text(resume_url)
    gemini_ans=ask_gemini(original_txt,[j["job_description"] for j in jobs])
    blocks=_split(gemini_ans,len(jobs)); out=[]
    for i,(job,blk) in enumerate(zip(jobs,blocks),1):
        try:
            if not blk or _norm(blk)=="NO_CHANGES_NEEDED":
                pdf=original_pdf; log.debug("Job %d: no changes",i)
            else:
                tex=tex_from_block(blk)
                pdf=compile_tex(tex) if tex else None
                if not pdf: pdf=original_pdf; log.warning("Job %d: fallback to original PDF",i)
            out.append({"job_url":job["job_url"],"resume_binary":base64.b64encode(pdf).decode()})
        except Exception as e:
            log.error("Job %d error %s – using original",i,e)
            out.append({"job_url":job["job_url"],"resume_binary":base64.b64encode(original_pdf).decode()})
    return out
# ╰───────────────────────────────────────────────────────────────╯

# ╭── File helpers & main ────────────────────────────────────────╮
def load_jobs(p:str):
    if not Path(p).exists():
        log.error("Job file not found: %s", p)
        return []
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    return [{"job_url":j.get("job_url") or j.get("jobUrl"),
             "job_description":j.get("job_description") or j.get("description")}
            for j in data if j.get("job_url") or j.get("jobUrl")]

def run_all(jfile:str,resume_url:str,batch=15):
    jobs=load_jobs(jfile)
    if not jobs:
        log.error("No jobs loaded. Exiting.")
        return []
    res=[]
    for i in range(0,len(jobs),batch):
        res+=process_batch(resume_url,jobs[i:i+batch])
        if i+batch<len(jobs): log.debug("Pause 30 s"); time.sleep(30)
    return res

if __name__=="__main__":
    RESUME_URL="https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/1753977528980_New%20Resume.pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS8xNzUzOTc3NTI4OTgwX05ldyBSZXN1bWUucGRmIiwiaWF0IjoxNzUzOTc3NzgxLCJleHAiOjE3NTQ1ODI1ODF9.7VB4p1cXBEJiRqlNz-WfibpQT5SYuGguU-olU9k4Al4"
    JOBS_JSON ="./linkedin_jobs_2025-07-31_17-35-34.json"
    OUT       ="tailored_resumes_batch_kv.json"
    results = run_all(JOBS_JSON, RESUME_URL)
    if results:
        Path(OUT).write_text(json.dumps(results,indent=2),encoding="utf-8")
        log.info("Done → %s",OUT)
    else:
        log.error("No output written due to previous errors.")
