import os
import tempfile
import requests
from sqlalchemy import create_engine, Column, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, declarative_base
import uuid
from datetime import datetime
from dotenv import load_dotenv
from difflib import SequenceMatcher
from docx import Document
import fitz  # PyMuPDF
import google.generativeai as genai
import time
from google.api_core import exceptions as google_exceptions
import subprocess
import shutil

# Load environment variables
load_dotenv()
DB_URL = os.getenv('DATABASE_URL')
GEMINI_API_KEY = os.getenv('GOOGLE_API')

if not DB_URL or not GEMINI_API_KEY:
    raise ValueError("DATABASE_URL and GOOGLE_API environment variables must be set.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# SQLAlchemy setup
Base = declarative_base()

class UploadedResume(Base):
    __tablename__ = "uploaded_resume"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_url = Column(Text)
    experience = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    users_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

def extract_text_from_pdf_response(response):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name
    try:
        doc = fitz.open(tmp_path)
        text = ""
        for page in doc:
            text += page.get_text()  # type: ignore[attr-defined]
        doc.close()
    finally:
        os.remove(tmp_path)
    return text

def extract_text_from_docx_response(response):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name
    try:
        doc = Document(tmp_path)
        text = "\n".join([para.text for para in doc.paragraphs])
    finally:
        os.remove(tmp_path)
    return text

def extract_resume_text(file_url):
    response = requests.get(file_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch file: {file_url}")
    content_type = response.headers.get('Content-Type', '').lower()
    url_path = file_url.lower().split('?')[0]
    if 'pdf' in content_type or url_path.endswith('.pdf'):
        return extract_text_from_pdf_response(response)
    elif 'word' in content_type or url_path.endswith('.docx') or url_path.endswith('.docx'):
        return extract_text_from_docx_response(response)
    else:
        raise Exception(f"Unsupported file type: {file_url}")

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def tailor_resume_with_gemini(original_text, job_description):
    prompt = f"""
    You are an expert resume writer and a LaTeX specialist. Your task is to analyze the following resume and job description.

    First, decide if the resume is already a good match for the job description.
    - If it is a good match and requires no significant changes, respond with only the text: NO_CHANGES_NEEDED
    - If it needs tailoring, rewrite the resume to perfectly match the job description. Emphasize relevant skills and experiences, and rephrase sections to align with the job's requirements.

    **Crucially, your output must be a complete, self-contained, and compilable LaTeX document.**

    Use the 'article' class with 11pt font. Use 'geometry' for margins (e.g., left=1in, right=1in, top=1in, bottom=1in) and 'titlesec' for professional section formatting. Ensure there are no page numbers. The entire resume should be in a single column.

    **Job Description:**
    {job_description}

    **Original Resume:**
    {original_text}

    **Your Response (as a complete LaTeX document or 'NO_CHANGES_NEEDED'):**
    """
    
    # DEBUG: Print the size of the prompt
    print(f"\n[DEBUG] Prompt size: {len(prompt)} characters. Sending to Gemini...")

    retries = 3
    delay = 20
    for i in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except google_exceptions.ResourceExhausted as e:
            if i < retries - 1:
                print(f"Rate limit exceeded. Retrying in {delay} seconds... ({i + 1}/{retries})")
                time.sleep(delay)
                delay *= 2
            else:
                print("\nGemini API quota exceeded. Please check your plan or wait and try again.")
                raise e
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise e

def compile_latex_to_pdf(latex_string, output_filename, resume_id):
    """
    Compiles a string of LaTeX code into a PDF file.
    Provides detailed error logging and saves failed files for debugging.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        base_name = "resume"
        tex_path = os.path.join(temp_dir, f"{base_name}.tex")
        log_path = os.path.join(temp_dir, f"{base_name}.log")
        pdf_path = os.path.join(temp_dir, f"{base_name}.pdf")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_string)

        # Run pdflatex twice to resolve any cross-references
        process = None
        for _ in range(2):
            try:
                process = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=30  # Add a timeout to prevent hangs
                )
            except FileNotFoundError:
                # This is a fallback check, though the main one should catch it.
                print("\n--- LaTeX Error ---")
                print("`pdflatex` command not found. Please ensure a LaTeX distribution (like MiKTeX) is installed and in your system's PATH.")
                return False
            except subprocess.TimeoutExpired:
                print("\n--- LaTeX Error ---")
                print("`pdflatex` command timed out. The LaTeX document may be too complex or have an error.")
                return False

        if process and process.returncode == 0 and os.path.exists(pdf_path):
            shutil.move(pdf_path, output_filename)
            return True
        else:
            # Compilation failed, so we save the logs for debugging
            print(f"\n--- LaTeX Compilation Failed for resume {resume_id} ---")
            failed_tex_path = f"failed_resume_{resume_id}.tex"
            failed_log_path = f"failed_resume_{resume_id}.log"
            
            shutil.copy(tex_path, failed_tex_path)
            if os.path.exists(log_path):
                shutil.copy(log_path, failed_log_path)

            print(f"The problematic LaTeX code has been saved to: {failed_tex_path}")
            print(f"The full compilation log has been saved to: {failed_log_path}")
            
            if process:
                print("\n--- Compiler Output (stdout) ---")
                print(process.stdout)
                if process.stderr:
                    print("\n--- Compiler Error (stderr) ---")
                    print(process.stderr)
            return False

if __name__ == "__main__":
    # Critical: Check for LaTeX installation at the very beginning
    if not shutil.which("pdflatex"):
        print("\n--- CRITICAL ERROR ---")
        print("`pdflatex` command not found. This script requires a LaTeX distribution (like MiKTeX for Windows or TeX Live for macOS/Linux) to be installed and included in your system's PATH.")
        print("Please install it and try again.")
        exit(1)

    print("Enter/paste the job description (end with a blank line):")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    job_description = " ".join(lines)
    if not job_description.strip():
        print("No job description provided. Exiting.")
        exit(1)

    resumes = session.query(UploadedResume).all()
    if not resumes:
        print("No resumes found in the database.")
        exit(1)

    for i, resume in enumerate(resumes):
        print(f"\n--- Processing Resume {i + 1}/{len(resumes)} (ID: {resume.id}) ---")
        try:
            original_text = extract_resume_text(resume.file_url)
            print("Sending to Gemini for LaTeX generation...")
            latex_output = tailor_resume_with_gemini(original_text, job_description)

            if latex_output == "NO_CHANGES_NEEDED":
                print("Gemini determined this resume is a good match. No changes made.")
            elif not latex_output.strip().startswith("\\documentclass"):
                print("Gemini did not return valid LaTeX. Skipping PDF generation.")
                print(f"Response: {latex_output}")
            else:
                output_file = f"tailored_resume_{resume.id}.pdf"
                print(f"Compiling LaTeX to {output_file}...")
                if compile_latex_to_pdf(latex_output, output_file, str(resume.id)):
                    print(f"Successfully created {output_file}")
                else:
                    print(f"Failed to create PDF for resume {resume.id}. Check the saved .tex and .log files for errors.")
        except Exception as e:
            print(f"An error occurred while processing resume {resume.id}: {e}")
    
    print("\nAll resumes have been processed.")