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
from fpdf import FPDF

# Load environment variables
load_dotenv()
DB_URL = os.getenv('DATABASE_URL')
if not DB_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

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
        doc.close()  # Ensure file is closed before deleting
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
    # Try to guess from content-type
    if 'pdf' in content_type:
        return extract_text_from_pdf_response(response)
    elif 'word' in content_type or 'docx' in content_type:
        return extract_text_from_docx_response(response)
    # Fallback: guess from URL (for old links or missing headers)
    url_path = file_url.lower().split('?')[0]
    if url_path.endswith('.pdf'):
        return extract_text_from_pdf_response(response)
    elif url_path.endswith('.docx'):
        return extract_text_from_docx_response(response)
    else:
        raise Exception(f"Unsupported file type: {file_url}")

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def tailor_resume(original_text, job_description):
    # Compute similarity
    sim = similarity(original_text, job_description)
    if sim > 0.7:
        print("\nResume already matches the job description well. No tailoring required.")
        return original_text, []

    # Extract words from job description
    job_words = set(word.lower().strip('.,;:') for word in job_description.split())
    resume_words = set(word.lower().strip('.,;:') for word in original_text.split())
    missing_keywords = sorted(list(job_words - resume_words))

    tailored = original_text
    added = []
    if missing_keywords:
        # Try to find a Skills section
        lines = original_text.splitlines()
        skills_idx = None
        for i, line in enumerate(lines):
            if 'skill' in line.lower():
                skills_idx = i
                break
        if skills_idx is not None:
            # Add missing keywords to the Skills section
            lines[skills_idx] += ", " + ", ".join(missing_keywords)
            tailored = "\n".join(lines)
            added = missing_keywords
        else:
            # No Skills section, add one at the end
            tailored += f"\n\nSkills: {', '.join(missing_keywords)}"
            added = missing_keywords
        print("\n--- Tailoring applied ---")
        print(f"Added to Skills section: {', '.join(missing_keywords)}")
    else:
        print("\nNo missing keywords from job description to add to Skills section.")
    return tailored, added

def save_pdf(text, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.splitlines():
        # Remove or replace non-latin-1 characters
        safe_line = line.encode("latin-1", "ignore").decode("latin-1")
        pdf.multi_cell(0, 10, safe_line)
    pdf.output(filename)

if __name__ == "__main__":
    print("Enter/paste the job description (end with a blank line):")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
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

    best_score = -1
    best_resume = None
    best_text = None
    for resume in resumes:
        try:
            text = extract_resume_text(resume.file_url)
            score = similarity(text, job_description)
            print(f"Resume {resume.id} score: {score:.2f}")
            if score > best_score:
                best_score = score
                best_resume = resume
                best_text = text
        except Exception as e:
            print(f"Error processing resume {resume.id}: {e}")

    if not best_resume:
        print("No suitable resume found.")
        exit(1)

    tailored_text, added_keywords = tailor_resume(best_text, job_description)
    if not added_keywords and similarity(best_text, job_description) > 0.7:
        print("No tailoring was necessary. Exiting without generating a new PDF.")
        exit(0)
    output_file = "tailored_resume.pdf"
    save_pdf(tailored_text, output_file)
    print(f"Tailored resume saved as {output_file}")