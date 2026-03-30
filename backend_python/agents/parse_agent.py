from config import GOOGLE_API, GROQ_API
import requests
import fitz
import io
from google import genai
from google.genai import types
from pdf2image import convert_from_bytes
import pytesseract
from pydantic import BaseModel
from typing import List, Optional

class LocationSchema(BaseModel):
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    full_location: Optional[str]

class UserContactSchema(BaseModel):
    first: Optional[str]
    last: Optional[str]
    email: Optional[str]
    phone: Optional[str]

class UserProfileSchema(BaseModel):
    titles: List[str]
    keywords: List[str]
    candidate_name: Optional[str]
    location: Optional[LocationSchema]
    user: Optional[UserContactSchema]
    general_experience_years: Optional[float]
    known_tech_experience_years: Optional[float]
    unknown_tech_experience_years: Optional[float]
    current_ctc: Optional[str]
    expected_ctc: Optional[str]
    notice_period: Optional[str]
    tech_stacks: List[str]
    tools: List[str]
    sure_skills: List[str]
    additional_skills: List[str]
client  = genai.Client(api_key= GOOGLE_API)
model = 'gemini-2.5-flash-lite'
# client = Groq(
#     api_key=GROQ_API,
# )
# model="llama-3.3-70b-versatile"

def parse_pdf(url : str):
    response = requests.get(url)
    if response.status_code != 200 :
        raise Exception("failed to fetch url")
    else:
        pdf_bytes = response.content
        docs = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        pages = len(docs)

        for page_num in range(pages):
            page = docs.load_page(page_num)
            page_text = page.get_text().strip()
            if page_text:
                text += page_text
            else:
                # Fallback to OCR using pdf2image + pytesseract on page bytes
                # Convert only the page to image
                images = convert_from_bytes(pdf_bytes)
                if images:
                    text_from_image = pytesseract.image_to_string(images[0])
                    if(text_from_image):
                        text += text_from_image
                        print("data fetched from resume using **tesseract**")
                    else:
                        print(f"unable to fetch the text from resume {page_num + 1}")
                else:
                    print(f"unable to convert the image from byte fallback method failed!")
        if len(text)< 500 or text.count('') > (len(text) / 2):
            print(text)
            raise ValueError("invalid pdf")
        print("data fetched from resume")


        docs.close()
        return text

system_instruction = """
You are an expert AI recruiter and resume parser.
Extract the comprehensive profile from the provided resume text.
Your output MUST perfectly match the provided JSON schema.

CRITICAL INSTRUCTIONS:
- TITLES: You MUST generate exactly 5 distinct, highly relevant job titles that this candidate is best suited for based on their skills and experience. Do not provide less than 5.
- ADDITIONAL SKILLS: You MUST strictly limit the `additional_skills` array to a MAXIMUM of 5 items. Do not output more than 5.
- Use null for missing strings, [] for empty lists.
- Do NOT invent any skills or tools not implied by or found in the resume text.
- candidate_name must be a string with all spaces replaced by underscores.
"""
              
def main(url):
    response: any
    if url:
            resume_text = (parse_pdf(url))
            contents = f"Resume Content for Analysis:\n{resume_text}"                       
            
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=UserProfileSchema
                )
            ).text
            
            import json
            try:
                parsed_json = json.loads(response)
            except Exception as e:
                # Fallback if markdown blocking occurs
                clean = response.replace('```json', '').replace('```', '').strip()
                parsed_json = json.loads(clean)
                
            return parsed_json 

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
if __name__ == "__main__":
    main("https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/1766914489015_AISHWARYA%20RESUME.pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS8xNzY2OTE0NDg5MDE1X0FJU0hXQVJZQSBSRVNVTUUucGRmIiwiaWF0IjoxNzY2OTE0NDkxLCJleHAiOjE3NzU1NTQ0OTF9.Uy4f9nrWkpLLWUPy1KPYJWU_8zqWJlnjp2n0hqGMI-E")