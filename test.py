import os
import tempfile
import requests
from sqlalchemy import create_engine, Column, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, declarative_base
import uuid
from datetime import datetime
from dotenv import load_dotenv
import json
import re
import google.generativeai as genai
import time
from google.api_core import exceptions as google_exceptions
import subprocess
import shutil
import platform
from docx import Document
import fitz  # PyMuPDF
from weasyprint import HTML

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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    body {{ font-family: sans-serif; margin: 0.5in; }}
    h1 {{ font-size: 24pt; text-align: center; margin-bottom: 5px; }}
    .contact-info {{ text-align: center; margin-bottom: 20px; color: #555; }}
    h2 {{ font-size: 14pt; border-bottom: 2px solid black; padding-bottom: 2px; margin-top: 20px; }}
    ul {{ padding-left: 20px; list-style-type: disc; }}
    li {{ margin-bottom: 5px; }}
    .project-header {{ font-weight: bold; }}
</style>
</head>
<body>
    <h1>{name}</h1>
    <div class="contact-info">{contact_line}</div>
    {sections_html}
</body>
</html>
"""

def simple_markdown_to_latex(text):
    """Converts simple markdown (bold) to LaTeX."""
    text = text.replace('&', r'\&').replace('%', r'\%').replace('$', r'\$').replace('#', r'\#').replace('_', r'\_')
    text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)
    return text

def create_latex_section(title, items):
    """Creates a LaTeX section with a list of items."""
    if not items:
        return ""
    
    section = f"\\section*{{{title}}}\n"
    section += "\\begin{itemize}[leftmargin=*,labelsep=0.5em, noitemsep]\n"
    for item in items:
        # Handle nested items if they exist
        if isinstance(item, dict) and 'header' in item:
            section += f"    \\item \\textbf{{{simple_markdown_to_latex(item['header'])}}}\n"
            if 'points' in item and item['points']:
                section += "    \\begin{itemize}[leftmargin=1.5em, noitemsep]\n"
                for point in item['points']:
                    section += f"        \\item {simple_markdown_to_latex(point)}\n"
                section += "    \\end{itemize}\n"
        else:
            section += f"    \\item {simple_markdown_to_latex(str(item))}\n"
    section += "\\end{itemize}\n"
    return section


def tailor_resume_with_gemini_html(original_text, job_description):
    prompt = f"""
    You are an expert resume writer. Your task is to analyze the provided resume and job description, then rewrite the resume content to perfectly match the job description.

    **CRITICAL INSTRUCTION:** Your output MUST be a valid JSON object. Do not add any explanatory text or markdown formatting around the JSON.

    The JSON object should have the following structure:
    {{
      "name": "Full Name",
      "contact_line": "Location | Email | Phone | LinkedIn URL",
      "summary": "A tailored professional summary as a single string. Use <strong> for bold text.",
      "sections": [
        {{ 
          "title": "Technical Skills", 
          "points": [ "<strong>Category:</strong> Skill 1, Skill 2", "<strong>Another Category:</strong> Skill A, Skill B" ] 
        }},
        {{ 
          "title": "Projects", 
          "points": [ 
            "<strong>Project Title:</strong> Description of responsibility 1.",
            "<strong>Another Project:</strong> Description of responsibility 2."
          ]
        }}
      ]
    }}

    If the original resume is already an excellent match and requires no changes, return this exact JSON object:
    {{ "no_changes_needed": true }}

    **Job Description:**
    {job_description}

    **Original Resume:**
    {original_text}

    **Your JSON Response:**
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

def generate_html_from_json(data):
    """Fills the HTML template with data from the JSON object."""
    sections_html = ""
    
    # Summary
    if data.get('summary'):
        sections_html += f"<h2>Summary</h2><p>{data['summary']}</p>"

    # Other sections
    for section_data in data.get('sections', []):
        title = section_data.get('title')
        points = section_data.get('points')
        if title and points:
            sections_html += f"<h2>{title}</h2><ul>"
            for point in points:
                sections_html += f"<li>{point}</li>"
            sections_html += "</ul>"

    # Fill the main template
    html_content = HTML_TEMPLATE.format(
        name=data.get('name', ''),
        contact_line=data.get('contact_line', ''),
        sections_html=sections_html
    )
    return html_content

def convert_html_to_pdf(html_string, output_filename):
    """Converts an HTML string to a PDF file using WeasyPrint."""
    try:
        HTML(string=html_string).write_pdf(output_filename)
        return True
    except Exception as e:
        print(f"\n--- PDF Generation Failed (WeasyPrint) ---")
        print(f"An error occurred: {e}")
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
            print("Sending to Gemini for JSON generation...")
            gemini_response = tailor_resume_with_gemini_html(original_text, job_description)

            try:
                # Clean up the response and parse JSON
                clean_response = gemini_response.strip().replace("```json", "").replace("```", "")
                resume_data = json.loads(clean_response)
            except json.JSONDecodeError:
                print("Gemini did not return valid JSON. Skipping PDF generation.")
                print(f"Full Response: {gemini_response}")
                continue

            if resume_data.get("no_changes_needed"):
                print("Gemini determined this resume is a good match. No changes made.")
                continue

            html_content = generate_html_from_json(resume_data)
            output_file = f"tailored_resume_{resume.id}.pdf"
            print(f"Generating PDF with WeasyPrint to {output_file}...")
            
            if convert_html_to_pdf(html_content, output_file):
                # --- THIS IS THE NEW, EXPLICIT "GIVE BACK" CODE ---
                print("\n-------------------------------------------------")
                print("✅ RESUME CREATED AND RETURNED TO YOU!")
                print(f"   Your tailored resume is located at:")
                print(f"   ==> {output_file}")
                print("-------------------------------------------------")
                
                # Attempt to open the PDF automatically for convenience
                print("\nAttempting to open the PDF automatically...")
                try:
                    if platform.system() == "Windows":
                        os.startfile(output_file)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", output_file], check=True)
                    else:  # Linux
                        subprocess.run(["xdg-open", output_file], check=True)
                    print("Success! The PDF should be open on your screen.")
                except Exception as e:
                    print(f"Could not open the PDF automatically. Please click the link above to open it manually.")
                    print(f"(Reason: {e})")
            else:
                print(f"Failed to create PDF for resume {resume.id}.")
        except Exception as e:
            print(f"An error occurred while processing resume {resume.id}: {e}")
    
    print("\nAll resumes have been processed.")