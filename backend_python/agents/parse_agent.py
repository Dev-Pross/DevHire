from config import GOOGLE_API
from database.SchemaModel import User, UploadedResume, ParsedTitle
from database.db_engine import Session
import requests
import fitz
import io
from google import genai
from google.genai import types
import uuid
import datetime

session = Session()
client  = genai.Client(api_key= GOOGLE_API)

def parse_pdf(url : str):
    response = requests.get(url)
    if response.status_code != 200 :
        raise Exception("failed to fetch url")
    else:
        # print(response.content)
        pdf = io.BytesIO(response.content)
        doc = fitz.open("pdf",pdf)

        text=""
        for page in doc:
            text+=page.get_text()
    return text

def resumeNotExist(resume_id : str):
    resume = session.query(ParsedTitle).filter(ParsedTitle.resume_id == resume_id).first()
    if resume :
        
        return False
    else:
        return True

email = "vamsi@gmail.com"
# print(email)


user = session.query(User.id).filter(User.email == email).first()
userID = user[0] 
print(userID)

if userID:
    UploadedResume = session.query(UploadedResume.file_url,UploadedResume.id).filter(UploadedResume.users_id== userID).first()
    resume = UploadedResume[0] if UploadedResume else None
    resume_id = UploadedResume[1] if UploadedResume else None
    # print(resume_id)
    if resume:
        resume_text = (parse_pdf(resume))
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite-preview-06-17",
            contents = f"""You are an AI hiring assistant helping with job matching based on resumes.
                    Your task is to analyze the following resume content and extract TWO separate lists:

                    1. **SUITABLE JOB TITLES** - Extract 5-8 powerful, specific job titles that comprehensively reflect the candidate's skills, experience, and seniority level.
                    2. **JOB KEYWORDS** - Extract up to 20 relevant keywords covering technologies, skills, tools, domains, and role-related terms.

                    📌 Guidelines for Job Titles:
                    - Include both direct job titles (e.g., "Frontend Developer") and adjacent roles (e.g., "UI Engineer")
                    - Consider seniority level (Junior/Mid/Senior/Lead/Principal) based on experience
                    - Include cross-domain titles if experience is multidisciplinary (e.g., "Full Stack Engineer", "DevOps Engineer")
                    - Focus on the most marketable and accurate titles
                    - Avoid generic titles (e.g., "Software Guy", "Developer")

                    📌 Guidelines for Keywords:
                    - Include programming languages, frameworks, libraries, and tools
                    - Add domain-specific terms (e.g., "Machine Learning", "Cloud Computing", "E-commerce")
                    - Include soft skills if clearly demonstrated (e.g., "Leadership", "Project Management")
                    - Add certifications, methodologies, and industry terms
                    - Include both technical and business-relevant keywords
                    - Cover keywords that support ALL the job titles listed

                    📥 Resume Text:
                    {resume_text}

                    ✅ Output Format:
                    Return ONLY the titles and keywords separated by "~" character in this exact format:

                    Senior Software Engineer, Full Stack Developer, Backend Engineer, Frontend Developer, DevOps Engineer~Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, MongoDB, PostgreSQL, REST APIs, Microservices, Agile, Git, CI/CD, Machine Learning, TensorFlow, Leadership, Project Management, Cloud Computing, System Design

                    Order both lists from most relevant to least relevant based on the resume content.""",
            config=types.GenerateContentConfig(
            temperature=0.65
            )
        )

        print(response.text)
        [titles,Keywords ]= response.text.split("~")
        # titles = [title.strip() for title in titles if titles] 
        print((titles))
        print(Keywords)

    # inserting data into tables
        # if resumeNotExist(resume_id):
        #     newTitles = ParsedTitle(
        #         id=uuid.uuid4(),
        #         resume_id=resume_id,
        #         titles= titles
        #     )
        #     session.add(newTitles)
        #     session.commit()
        #     print("data inserted in parsed table")
        # else:
        #     print("titles already exists")