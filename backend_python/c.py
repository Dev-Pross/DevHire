import requests
import tempfile
import os
import base64
import uuid
import time
import json
import re
from docx import Document
from config import GOOGLE_API
import fitz # PyMuPDF, for PDF
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# --------------------------------------
# Setup Gemini model
if not GOOGLE_API:
    raise ValueError("Missing Gemini API key as GOOGLE_API env var.")

genai.configure(api_key=GOOGLE_API)
model = genai.GenerativeModel('gemini-2.5-flash')

# --------------------------------------
# Resume Extraction Helpers

def extract_text_from_pdf_response(response):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name
    try:
        doc = fitz.open(tmp_path)
        text = ""
        for page in doc:
            text += page.get_text()
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
    elif 'word' in content_type or url_path.endswith('.docx'):
        return extract_text_from_docx_response(response)
    else:
        raise Exception(f"Unsupported file type: {file_url}")

# --------------------------------------
# Batch Prompt Builder

def build_batch_prompt(original_text, job_descriptions):
    sample_latex = r'''
\documentclass[11pt]{article}
\usepackage{geometry}
\geometry{letterpaper, margin=0.8in}
\setlength{\parindent}{0pt}
\begin{document}
\begin{center}
{\LARGE \textbf{John Doe}}\\
Email: john.doe@email.com \\
Phone: +91-1234567890 \\
\end{center}

\section*{Professional Summary}
{\small
A skilled Java and React developer with over 5 years of experience...
}

\section*{Technical Skills}
{\small
Languages: Java, JavaScript, Python\\
Frameworks: React, Spring Boot, Node.js\\
Databases: MySQL, MongoDB\\
}

\section*{Experience}
{\small
\textbf{Software Developer} | ABC Company | 2020-Present\\
- Developed web applications using Java and React\\
- Worked with databases and APIs\\
}

\section*{Education}
{\small
\textbf{Bachelor of Technology in Computer Science}\\
XYZ University | 2016-2020\\
}
\end{document}
'''
    
    prompt = f"""
You are an expert resume writer. You will tailor one resume to multiple job descriptions in a single response.

Here is the original resume:
{original_text}

I will provide you with multiple job descriptions. For each job, you need to either:
1. Return "NO_CHANGES_NEEDED" if the resume already fits perfectly
2. Return a complete LaTeX resume starting with \\documentclass that is tailored for that specific job

IMPORTANT: Separate each job response with the exact marker "=== JOB n ===" where n is the job number (1, 2, 3, etc.)

Sample LaTeX format to follow:
{sample_latex}

Job Descriptions:
"""
    
    # Add numbered job descriptions
    for i, desc in enumerate(job_descriptions, 1):
        prompt += f"\n=== JOB {i} ===\n{desc}\n"
    
    prompt += f"""
\nNow please provide tailored resumes for all {len(job_descriptions)} jobs above. Remember to separate each response with "=== JOB n ===" markers.
"""
    
    return prompt

# --------------------------------------
# Batch AI Tailoring Function with DEBUG

def tailor_resumes_batch_with_gemini(original_text, job_descriptions):
    prompt = build_batch_prompt(original_text, job_descriptions)
    retries = 3
    delay = 20
    
    for i in range(retries):
        try:
            response = model.generate_content(prompt)
            gemini_text = response.text.strip()
            
            # DEBUG: Save Gemini response to file
            timestamp = int(time.time())
            debug_file = f"gemini_response_debug_{timestamp}.txt"
            
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(gemini_text)
            
            print(f"DEBUG: Gemini response saved to {debug_file}")
            
            return gemini_text
            
        except google_exceptions.ResourceExhausted:
            if i < retries - 1:
                print(f"Rate limited, waiting {delay} seconds...")
                time.sleep(delay)
                delay *= 2
            else:
                raise
        except Exception as e:
            print(f"Gemini API error: {e}")
            raise

# --------------------------------------
# Parse Batch Response

def parse_batch_gemini_response(text, job_count):
    """
    Parses Gemini output split by '=== JOB n ===' markers.
    Returns list of LaTeX strings or "NO_CHANGES_NEEDED" strings.
    """
    # Split by job markers
    pattern = r"=== JOB (\d+) ==="
    parts = re.split(pattern, text)
    
    # parts will be like: ['initial_text', '1', 'job1_content', '2', 'job2_content', ...]
    job_contents = {}
    
    # Process pairs of (job_number, content)
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            job_num = int(parts[i])
            content = parts[i + 1].strip()
            job_contents[job_num] = content
    
    # Return ordered list
    results = []
    for job_index in range(1, job_count + 1):
        content = job_contents.get(job_index, "")
        results.append(content)
    
    return results

# --------------------------------------
# ENHANCED LaTeX Compilation with Multiple Endpoints

def compile_latex_to_pdf(latex_string, job_id=None):
    """Compile LaTeX using multiple reliable online endpoints"""
    
    # Enhanced list of LaTeX compilation endpoints
    endpoints = [
        {
            "name": "LaTeX Online (Primary)",
            "url": "https://latexonline.cc/compile",
            "method": "original",
        },
        {
            "name": "YtoTech LaTeX",
            "url": "https://latex.ytotech.com/builds/sync",
            "method": "original",
        },
        {
            "name": "API LaTeX Online",
            "url": "https://api.latexonline.cc/compile", 
            "method": "original",
        },
        {
            "name": "TeXLive Online",
            "url": "https://texlive.net/run",
            "method": "texlive",
        },
        {
            "name": "LaTeX CGI",
            "url": "https://latex.codecogs.com/pdf.download",
            "method": "direct_post",
        }
    ]
    
    for i, endpoint in enumerate(endpoints):
        try:
            print(f"Trying endpoint {i+1}/{len(endpoints)}: {endpoint['name']}")
            
            if endpoint["method"] == "original":
                files = {'texfile': ('document.tex', latex_string)}
                data = {'command': 'pdflatex'}
                response = requests.post(
                    endpoint["url"], 
                    files=files, 
                    data=data, 
                    timeout=120,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                
            elif endpoint["method"] == "texlive":
                files = {'file': ('main.tex', latex_string)}
                data = {'format': 'pdf', 'engine': 'pdflatex'}
                response = requests.post(
                    endpoint["url"],
                    files=files,
                    data=data,
                    timeout=120,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                
            elif endpoint["method"] == "direct_post":
                response = requests.post(
                    endpoint["url"],
                    data=latex_string,
                    timeout=120,
                    headers={
                        'Content-Type': 'application/x-latex',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
            
            # Check if we got a valid PDF
            if response.status_code >= 200 and response.status_code < 300:
                if len(response.content) > 1000 and response.content.startswith(b'%PDF'):
                    print(f"✅ Successfully compiled with {endpoint['name']}")
                    return response.content
                else:
                    print(f"❌ Invalid PDF response from {endpoint['name']}")
            else:
                print(f"❌ HTTP {response.status_code} from {endpoint['name']}")
                
        except Exception as e:
            print(f"❌ Exception at {endpoint['name']}: {e}")
            continue
    
    # If all endpoints fail, return None and handle gracefully
    print("⚠️ All LaTeX endpoints failed")
    return None

# --------------------------------------
# Single Resume Tailoring (for backward compatibility)

def tailor_resume_and_return_kv(file_url, job_description, job_url):
    """
    Single resume tailoring - for backward compatibility
    """
    return run_batch_tailoring_efficient_single(file_url, [{"job_url": job_url, "job_description": job_description}])[0]

# --------------------------------------
# Main Batch Processing Function

def run_batch_tailoring_efficient_single(resume_url, jobs_list):
    """
    Process a batch of jobs (up to 15) with single Gemini call
    
    Args:
        resume_url: URL to original resume
        jobs_list: List of {"job_url": str, "job_description": str}
    
    Returns:
        List of {"job_url": str, "resume_binary": str (base64)}
    """
    if len(jobs_list) > 15:
        raise ValueError("Maximum 15 jobs per batch")
    
    print(f"Processing batch of {len(jobs_list)} jobs...")
    
    # Extract original resume text once
    original_text = extract_resume_text(resume_url)
    
    # Prepare data
    job_descriptions = [job["job_description"] for job in jobs_list]
    job_urls = [job["job_url"] for job in jobs_list]
    
    # Single Gemini batch call
    print("Calling Gemini for batch tailoring...")
    gemini_response = tailor_resumes_batch_with_gemini(original_text, job_descriptions)
    
    # Parse batch results
    print("Parsing Gemini response...")
    tailored_texts = parse_batch_gemini_response(gemini_response, len(jobs_list))
    
    # Process each tailored result
    results = []
    for i, (job_url, tailored_text) in enumerate(zip(job_urls, tailored_texts)):
        print(f"Processing result {i+1}/{len(jobs_list)}: {job_url[:50]}...")
        
        try:
            if "NO_CHANGES_NEEDED" in tailored_text:
                # Use original resume
                response = requests.get(resume_url)
                if response.status_code == 200:
                    pdf_binary = response.content
                else:
                    raise RuntimeError(f"Could not download original resume")
            else:
                # Extract and compile LaTeX
                latex_code = extract_latex_from_text(tailored_text)
                if not latex_code:
                    raise RuntimeError(f"Could not extract LaTeX for job {i+1}")
                
                pdf_binary = compile_latex_to_pdf(latex_code, job_id=f"batch_{i}")
                
                # If LaTeX compilation failed, use original resume as fallback
                if pdf_binary is None:
                    print(f"🔄 LaTeX compilation failed for job {i+1}, using original resume as fallback")
                    response = requests.get(resume_url)
                    if response.status_code == 200:
                        pdf_binary = response.content
                    else:
                        raise RuntimeError(f"Could not download original resume as fallback")
            
            # Convert to base64
            resume_b64 = base64.b64encode(pdf_binary).decode("utf-8")
            results.append({
                "job_url": job_url,
                "resume_binary": resume_b64
            })
            print(f"✅ Successfully processed job {i+1}")
            
        except Exception as e:
            print(f"❌ Failed to process job {i+1}: {e}")
            
            # Try to use original resume as final fallback
            try:
                print(f"🔄 Using original resume as final fallback for job {i+1}")
                response = requests.get(resume_url)
                if response.status_code == 200:
                    pdf_binary = response.content
                    resume_b64 = base64.b64encode(pdf_binary).decode("utf-8")
                    results.append({
                        "job_url": job_url,
                        "resume_binary": resume_b64
                    })
                    print(f"✅ Fallback successful for job {i+1}")
                else:
                    print(f"❌ Final fallback also failed for job {i+1}")
                    continue
            except Exception as fallback_error:
                print(f"❌ Final fallback failed for job {i+1}: {fallback_error}")
                continue
    
    return results

def extract_latex_from_text(text):
    """Extract LaTeX code from text"""
    # Try fenced code block first
    if "```latex" in text:
        parts = text.split("```latex")
        if len(parts) > 1:
            latex_code = parts[1].split("```")
            return latex_code.strip()
    
    # Try to find \documentclass as fallback
    start_index = text.find("\\documentclass")
    if start_index != -1:
        return text[start_index:].strip()
    
    return None

# --------------------------------------
# Load Jobs from JSON

def load_jobs(json_path):
    """Load jobs from JSON file"""
    with open(json_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    
    # Normalize field names and filter valid jobs
    normalized_jobs = []
    for job in jobs:
        job_url = job.get("job_url") or job.get("jobUrl")
        job_description = job.get("job_description") or job.get("description")
        
        if job_url and job_description:
            normalized_jobs.append({
                "job_url": job_url,
                "job_description": job_description
            })
    
    return normalized_jobs

# --------------------------------------
# Main Batch Processing with JSON File

def run_batch_tailoring_from_json(json_path, resume_url, batch_size=15):
    """
    Process all jobs from JSON file in batches
    """
    jobs = load_jobs(json_path)
    all_results = []
    
    print(f"Loaded {len(jobs)} jobs from {json_path}")
    
    # Process in batches
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        print(f"\n=== Processing Batch {batch_num} ({len(batch)} jobs) ===")
        
        try:
            batch_results = run_batch_tailoring_efficient_single(resume_url, batch)
            all_results.extend(batch_results)
            print(f"✅ Batch {batch_num} completed: {len(batch_results)} resumes generated")
            
            # Add delay between batches to respect rate limits
            if i + batch_size < len(jobs):
                print("Waiting 30 seconds before next batch...")
                time.sleep(30)
                
        except Exception as e:
            print(f"❌ Batch {batch_num} failed: {e}")
            continue
    
    return all_results

# --------------------------------------
# Main Execution

if __name__ == "__main__":
    # Configuration
    resume_url = "https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/1753977528980_New%20Resume.pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS8xNzUzOTc3NTI4OTgwX05ldyBSZXN1bWUucGRmIiwiaWF0IjoxNzUzOTc3NzgxLCJleHAiOjE3NTQ1ODI1ODF9.7VB4p1cXBEJiRqlNz-WfibpQT5SYuGguU-olU9k4Al4"
    jobs_json_file = "./linkedin_jobs_2025-07-31_17-35-34.json"
    batch_size = 15  # Process 15 jobs per Gemini call
    
    try:
        # Run batch processing
        all_results = run_batch_tailoring_from_json(jobs_json_file, resume_url, batch_size)
        
        # Save results
        output_file = "tailored_resumes_batch_kv.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n🎉 Batch processing complete!")
        print(f"📊 Total jobs processed: {len(all_results)}")
        print(f"💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")
