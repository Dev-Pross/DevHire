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

email = "tejabudumuru3@gmail.com"
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
            contents=f"""You are an AI hiring assistant helping with job matching based on resumes.
            Your task is to analyze the following resume content and extract *suitable job titles* that comprehensively reflect the candidate's skills, experience, technologies, certifications, and roles — even if the titles are not explicitly mentioned in the resume.
            📌 Guidelines:
            - Include both direct job titles (e.g., “Frontend Developer”) and adjacent roles (e.g., “UI Engineer” if applicable).
            - Consider programming languages, frameworks, tools, and domains used.
            - Include junior/senior/lead prefixes if appropriate based on experience.
            - If experience is multidisciplinary, include cross-domain titles (e.g., “AI Product Analyst”, “ML Ops Engineer”).
            - Avoid generic or irrelevant titles (e.g., “Software Guy”).
            📥 Resume Text:
           
            {resume_text}
            
            ✅ Output Format:
            Return a bullet list of max number of possible job titles ordered by most relevant to least relevant, based on the resume content.
            Each title should be just the title string, no descriptions.""",
            config=types.GenerateContentConfig(
            temperature=0.65
            )
        )

        print(response.text)
    
        titles = [title.strip() for title in response.text.split("*") if title.strip()] 
        print((titles))

    # inserting data into tables
        # titles = ['Full-Stack Developer', 'MERN Stack Developer', 'Software Engineer', 'Web Developer', 'Backend Developer', 'Frontend Developer', 'Java Developer', 'Python Developer', 'AI Engineer', 'Cloud Engineer', 'Software Developer', 'Junior Full-Stack Developer', 'Junior Software Engineer']
        if resumeNotExist(resume_id):
            newTitles = ParsedTitle(
                id=uuid.uuid4(),
                resume_id=resume_id,
                titles= titles
            )
            session.add(newTitles)
            session.commit()
            print("data inserted in parsed table")
        else:
            print("titles already exists")