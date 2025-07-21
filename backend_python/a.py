from config import DB_URL, GOOGLE_API 
from database.db_engine import Session
from database.SchemaModel import UploadedResume
import os
import subprocess
import tempfile
import shutil    
import requests
from docx import Document # type: ignore
import fitz  # PyMuPDF
import google.generativeai as genai
import time
from google.api_core import exceptions as google_exceptions



# Load environment variables
GEMINI_API_KEY = GOOGLE_API

if not DB_URL or not GEMINI_API_KEY:
    raise ValueError("DATABASE_URL and GOOGLE_API environment variables must be set.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')


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


def tailor_resume_with_gemini(original_text, job_description):

    sample_latex = r'''\documentclass[letterpaper,11pt]{article}
    \usepackage{latexsym}
    \usepackage[empty]{fullpage}
    \usepackage{titlesec}
    \usepackage{marvosym}
    \usepackage[usenames,dvipsnames]{color}
    \usepackage{verbatim}
    \usepackage{enumitem}
    \usepackage[hidelinks]{hyperref}
    \usepackage{fancyhdr}
    \usepackage[english]{babel}
    \usepackage{tabularx}
    \input{glyphtounicode}
    \pagestyle{fancy}
    \fancyhf{} 
    \renewcommand{\headrulewidth}{0pt}
    \renewcommand{\footrulewidth}{0pt}
    \addtolength{\oddsidemargin}{-0.5in}
    \addtolength{\evensidemargin}{-0.5in}
    \addtolength{\textwidth}{1in}
    \addtolength{\topmargin}{-.5in}
    \addtolength{\textheight}{1.0in}
    \urlstyle{same}
    \raggedbottom
    \raggedright
    \setlength{\tabcolsep}{0in}
    \titleformat{\section}{\scshape\large}{}{0em}{}[\titlerule]
    \newcommand{\resumeSubheading}[4]{
    \item
        \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
        \textbf{#1} & #2 \\
        \textit{\small#3} & \textit{\small #4}
        \end{tabular*}
    }
    \newcommand{\resumeItem}[1]{\item\small{#1}}
    \newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]} 
    \newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
    \newcommand{\resumeItemListStart}{\begin{itemize}}
    \newcommand{\resumeItemListEnd}{\end{itemize}}
    %-------------------------------------------
    %%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%
    \begin{document}
    %----------HEADING----------
    \begin{center}
        \textbf{\Huge \scshape Saragadam Vamshi} \\ \vspace{1pt}
        Visakhapatnam, India \\
        \small +91-9381721427 $|$ \href{mailto:iamvamsi0@gmail.com}{\underline{iamvamsi0@gmail.com}} $|$ 
        \href{https://linkedin.com}{\underline{LinkedIn}} $|$ 
        \href{https://github.com}{\underline{GitHub}}
    \end{center}
    %-----------CAREER OBJECTIVE-----------
    \section*{Professional Summary}
    A motivated Computer Science graduate with a strong foundation in web development and software engineering. Proficient in designing and implementing responsive user interfaces using \textbf{HTML5}, \textbf{CSS3}, \textbf{JavaScript (ES6+)}, and \textbf{Python}. Experienced in integrating RESTful APIs and adhering to Agile methodologies to deliver efficient and scalable solutions. Demonstrates excellent problem-solving abilities, effective communication skills, and a commitment to continuous learning. Eager to contribute to Mahindra's innovative projects and drive positive change through technology.
    \section{Education}
    \resumeSubHeadingListStart
    \resumeSubheading
    {MVGR College of Engineering}{Vizianagaram, India}
    {B.Tech in Computer Science and Engineering; CGPA: 7.02/10}{May 2025}
    \resumeSubheading
        {Government Polytechnic College}{Anakapalle, India}
        {Diploma in Computer Engineering; Final Grade: 80\%}{June 2022}
    \resumeSubHeadingListEnd
    %-----------TECHNICAL SKILLS-----------
    \section{Technical Skills}
    \resumeSubHeadingListStart
    \resumeItem{\textbf{Frontend:} HTML, CSS, JavaScript, React, ExpressJs}
    \resumeItem{\textbf{Languages:} Python, Core Java}
    \resumeItem{\textbf{Concepts:} Data Structures, LLM}
    \resumeItem{\textbf{Tools:} MS Office, Git, GitHub, Linux, NodeJs} 
    \resumeItem{\textbf{Soft Skills:} Analytical Thinking, Communication, Team Collaboration}
    \resumeSubHeadingListEnd
    %-----------PROJECTS-----------
    \section{Projects}
    \resumeSubHeadingListStart
    \resumeSubheading
    {Grog Social Scribe}{Feb 2024 -- May 2024}
    {Frontend Developer}
    {\href{http://grog-social-scribe.lovable.app/} {grog-social-app}}
    \resumeItemListStart
    \resumeItem{Partnered closely with UX/UI designers to implement pixel-perfect, responsive web layouts utilizing 	\textbf{HTML5}, 	\textbf{CSS3} (Flexbox \& Grid), and 	\textbf{JavaScript (ES6+)}.}
    \resumeItem{Architected and developed modular JavaScript components to handle user input, asynchronously communicate with AI-driven REST APIs, and render dynamic content seamlessly.}
    \resumeItem{Instituted robust client-side validation and error recovery mechanisms, improving form submission success rates by over 	\textbf{30\%}.}
    \resumeItem{Enhanced performance through optimized DOM operations and lazy loading strategies, achieving a 	\textbf{25\% faster} initial render across desktop and mobile platforms.}
    \resumeItem{Adopted BEM methodology to structure CSS, promoting maintainability and enabling rapid style updates during iterative design sprints.}
    \resumeItem{Authored detailed technical documentation and led bi-weekly code reviews, ensuring adherence to coding standards and fostering team knowledge sharing.}
    \resumeItemListEnd
    \resumeSubHeadingListEnd
    %-----------ADDITIONAL INFO-----------
    \section{Additional Information}
    \resumeSubHeadingListStart
    \resumeItem{\textbf{Languages:} English (Fluent), Telugu (Native)}
    \resumeItem{\textbf{Interests:} Exploring frontend frameworks (React), LeetCode problem solving}
    \resumeSubHeadingListEnd
    \end{document}
    '''

    prompt = f"""
    You are an expert resume writer and a LaTeX specialist. Your task is to analyze the following resume and job description.

    First, decide if the resume is already a good match for the job description.
    - If it is a good match and requires no significant changes, respond with only the text: NO_CHANGES_NEEDED
    - If it needs tailoring, rewrite the resume to perfectly match the job description. Emphasize relevant skills and experiences, and rephrase sections to align with the job's requirements.

    **Crucially, your output must be a complete, self-contained, and compilable LaTeX document.**

    Use the 'article' class with 11pt font. Use 'geometry' for margins and 'titlesec' for professional section formatting.
    
    **CRITICAL INSTRUCTIONS FOR LATEX FORMATTING:**
    1.  Always load the `textcomp` packages (`\\usepackage{{textcomp}}`) to support common symbols and dont use odd colors.
    2.  You MUST properly escape all special LaTeX characters, especially `&`, `$`, `%`, `#`, and `_`. For example, an ampersand must be written as `\\&`.
    3.  Ensure the entire document is in a single column and has no page numbers (`\\pagestyle{{empty}}`)
    4.  Make sure the document maintain proper margins and spacing and Headings.
    5.  DONT ADD ADDITION SKILLS WHICH ARE NOT MENTIONED IN USER RESUME AND REMOVE DATES FOR PROJECT SECTION.
     
    

    **Job Description:**
    {job_description}

    **Original Resume:**
    {original_text}

    **Here is the Sample Resume, use the below LaTex code for reference purpose only (for format font styling etc) :**
    {sample_latex}

    **Your Response (as a complete LaTeX document or 'NO_CHANGES_NEEDED'):**
    ** MAINTAIN PROPER SYNTAX FOR OUTPUT**
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
    Compile LaTeX to PDF using multiple online endpoints
    """
    # Working endpoints based on search results
    endpoints = [
        'https://latexonline.cc/compile',
        'https://latex.ytotech.com/builds/sync',
        'https://api.latexonline.cc/compile'  # Additional endpoint to try
    ]
    
    max_retries = 2
    
    for endpoint_idx, endpoint in enumerate(endpoints, 1):
        print(f"Trying endpoint {endpoint_idx}/{len(endpoints)}: {endpoint}")
        
        for attempt in range(max_retries):
            try:
                print(f"  Attempt {attempt + 1}/{max_retries} for resume {resume_id}...")
                
                # Prepare the request
                files = {'texfile': ('document.tex', latex_string)}
                data = {'command': 'pdflatex'}
                
                # Make the request
                response = requests.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=90  # Increased timeout for compilation
                )
                
                print(f"  Response status: {response.status_code}")
                
                # Check if successful
                if response.status_code >= 200 and response.status_code < 300:
                    # Check if response content is actually a PDF
                    if len(response.content) > 1000 and response.content.startswith(b'%PDF'):
                        with open(output_filename, 'wb') as f:
                            f.write(response.content)
                        print(f"✅ PDF generated successfully using {endpoint}")
                        print(f"   File: {output_filename}")
                        return True
                    else:
                        print(f"  Response doesn't appear to be a valid PDF")
                        # Print first 200 chars of response for debugging
                        print(f"  Response preview: {response.text[:200]}")
                
                elif response.status_code == 400:
                    print(f"  Bad request - likely LaTeX compilation error")
                    print(f"  Error response: {response.text}")
                    break  # Don't retry for compilation errors
                
                elif response.status_code == 404:
                    print(f"  Endpoint not found - trying next endpoint")
                    break  # Try next endpoint
                
                elif response.status_code in [500, 502, 503, 504]:
                    print(f"  Server error ({response.status_code}) - retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                
                else:
                    print(f"  Unexpected status code: {response.status_code}")
                    print(f"  Response: {response.text[:200]}")
                    
            except requests.exceptions.Timeout:
                print(f"  Request timed out")
                if attempt < max_retries - 1:
                    print(f"  Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                    
            except requests.exceptions.RequestException as e:
                print(f"  Network error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                    
            except Exception as e:
                print(f"  Unexpected error: {e}")
                break
        
        print(f"  All attempts failed for {endpoint}")
    
    print(f"❌ All endpoints failed for resume {resume_id}")
    return False

def check_clsi_available():
    """Check if CLSI is running locally"""
    try:
        response = requests.get('http://localhost:3013/status', timeout=5)
        return response.status_code == 200
    except:
        return False

def try_latex_endpoint(endpoint, latex_string, output_filename):
    """Try a specific LaTeX online endpoint"""
    try:
        response = requests.post(
            endpoint,
            files={'texfile': ('document.tex', latex_string)},
            data={'command': 'pdflatex'},
            timeout=60
        )
        
        if response.status_code == 200 and len(response.content) > 1000:
            with open(output_filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ Success with {endpoint}")
            return True
    except Exception as e:
        print(f"Failed {endpoint}: {e}")
    return False


if __name__ == "__main__":

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
            gemini_response = tailor_resume_with_gemini(original_text, job_description)

            if "NO_CHANGES_NEEDED" in gemini_response:
                print("Gemini determined this resume is a good match. No changes made.")
                continue

            # --- Intelligent LaTeX Extraction ---
            # Handles cases where Gemini adds explanatory text or markdown fences.
            latex_code = None
            if "```latex" in gemini_response:
                # Extract from markdown block
                parts = gemini_response.split("```latex")
                if len(parts) > 1:
                    latex_code = parts[1].split("```")[0].strip()
            else:
                # Find the start of the document class
                start_index = gemini_response.find("\\documentclass")
                if start_index != -1:
                    latex_code = gemini_response[start_index:].strip()
            
            if not latex_code:
                print("Could not extract valid LaTeX from Gemini's response. Skipping PDF generation.")
                print(f"Full Response: {gemini_response}")
                continue

            with open(f"resume{i}.tex", 'wb') as f:
                f.write(latex_code.encode('utf-8'))
            output_file = f"tailored_resume_{resume.id}.pdf"
            print(f"Compiling extracted LaTeX to {output_file}...")
            if compile_latex_to_pdf(latex_code, output_file, str(resume.id)):
                # --- THIS IS THE NEW, EXPLICIT "GIVE BACK" CODE ---
                print("\n-------------------------------------------------")
                print("✅ RESUME CREATED AND RETURNED TO YOU!")
                print(f"   Your tailored resume is located at:")
                # print(f"   ==> {absolute_pdf_path}")
                print("-------------------------------------------------")
                
                # Attempt to open the PDF automatically for convenience
                # print("\nAttempting to open the PDF automatically...")
                # try:
                #     if platform.system() == "Windows":
                #         os.startfile(absolute_pdf_path)
                #     elif platform.system() == "Darwin":  # macOS
                #         subprocess.run(["open", absolute_pdf_path], check=True)
                #     else:  # Linux
                #         subprocess.run(["xdg-open", absolute_pdf_path], check=True)
                #     print("Success! The PDF should be open on your screen.")
                # except Exception as e:
                #     print(f"Could not open the PDF automatically. Please click the link above to open it manually.")
                #     print(f"(Reason: {e})")
            else:
                print(f"Failed to create PDF for resume {resume.id}. Check the saved .tex and .log files for errors.")
        except Exception as e:
            print(f"An error occurred while processing resume {resume.id}: {e}")
    
    print("\nAll resumes have been processed.")