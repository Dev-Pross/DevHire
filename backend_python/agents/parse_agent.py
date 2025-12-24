from config import GOOGLE_API, GROQ_API
import requests
import fitz
import io
from google import genai
from google.genai import types
# from groq import Groq


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
        # print(response.content)
        pdf = io.BytesIO(response.content)
        doc = fitz.open("pdf",pdf)

        text=""
        for page in doc:
            text+=page.get_text()
    return text

system_instruction = """
        You are an expert AI recruiter and resume analyzer.

        Your task is to analyze the provided resume text and generate two outputs that maximize the candidate’s visibility and job matching potential:

        1. Generate 5 high-quality, market-aligned job titles that reflect the candidate’s skills and experience.

        2. Extract 20-25 precise keywords optimized for ATS and recruiter searches.

        Important instructions for job titles:

        - If the candidate does not have confirmed professional work experience or only lists academic or personal projects, classify them as "Fresher" or "Entry Level".
        - Generate only junior-level job titles such as "Software Engineer", " Developer", "Frontend Developer","Full Stack Developer" dont use Senior as a prefix of Job titles untill unless candidate has professional work experience not personal project's experience thats it.
        - Do NOT suggest "Senior", "Lead", "Manager", or other advanced roles unless there is clear evidence of such experience in the resume.
        - Base the job title recommendations strictly on the experience and evidence provided in the resume.

        For keywords extraction:

        - Extract technical skills, domain knowledge, soft skills, certifications, emerging technologies, and business acumen terms.
        - Include keywords that reflect the candidate’s actual experience without fabricating information.

        Please return ONLY the following output format:

        <Job Titles (comma separated)>~<Keywords (comma separated)>

        Maintain the "~" separator without quotes and no additional text.
        """
            # for attempt in range(3):
# def resumeNotExist(resume_id : str):

#     resume = session.query(ParsedTitle).filter(ParsedTitle.resume_id == resume_id).first()
#     if resume :
        
#         return False
#     else:
#         return True

              
def main(url):
    response: any
    # userID = user
    if url:
        # UploadedResume = session.query(UploadedResume.file_url,UploadedResume.id).filter(UploadedResume.users_id== userID).first()
            resume_text = (parse_pdf(url))
            contents =f"""You are an Elite AI Talent Intelligence Engine designed for ruthless accuracy in candidate profiling. Your goal is to analyze the provided resume and extract precise metadata for algorithmic job matching. You must ignore fluff,experience levels, detect exaggeration, and map skills to the current global market reality.

                        INPUT CONTEXT:
                        Resume Text: {resume_text}

                        YOUR MISSION:
                        Generate exactly TWO data sets based on the resume:
                        1. 5 Strategic Job Titles (Ranked by fit)
                        2. 30-50 High-Value Keywords (Accurate with resume)

                        CRITICAL RULES FOR ANALYSIS (BE BRUTAL & HONEST):
                        ***[IMPORTANT] ALL TITLES SHOULD BE DEAD ACCURATE AND CONSISTENT *** 
                        1. SENIORITY CALIBRATION (Strict Enforcement):
                        - IF the candidate lists only personal projects, freelance gigs without verifiable company entities, or university projects: You MUST classify them as "Entry Level," "Junior," or "Associate." DO NOT assign "Senior," "Lead," or "Architect" titles, regardless of project complexity.
                        - IF the candidate has < 2 years of corporate experience: Use just titles no need of "Junior" and all things.
                        - IF the candidate has 3-5 years: Use "Mid-Level" or standard Engineer titles.
                        - ONLY assign "Senior" or "Lead" if there is clear evidence of team leadership and 5+ years of corporate experience.

                        2. JOB TITLE STRATEGY (Generate 5 Titles):
                        - Title 1 (The Perfect Match): The most accurate title based on actual work history.
                        - Title 2 (The Specialist): A title highlighting their strongest specific tech stack (e.g., "React Developer" or "Python Backend Engineer").
                        - Title 3 (The Market Trend): A modern, high-demand title that fits their skills (e.g., "AI Application Engineer" vs "Programmer").
                        - Title 4 (The Growth Role): A slightly aspirational title they are qualified for (e.g., moving from "Developer" to "Engineer").
                        - Title 5 (The Industry Hybrid): A title mixing domain + tech if applicable (e.g., "FinTech Developer"), otherwise a standard variation.

                        3. KEYWORD EXTRACTION STRATEGY (30-50 Keywords):
                        - PRIORITY 1 (Hard Tech Stack): Languages, Frameworks, Databases, Cloud Tools. (e.g., usage of "MERN" should explode into "MongoDB, Express.js, React, Node.js").
                        - PRIORITY 2 (Concepts): Methodologies (CI/CD, Agile, REST API, Microservices).
                        - PRIORITY 3 (Tools): Git, Docker, Kubernetes, Jira, Postman.
                        - NORMALIZE TERMS: Convert "React.js" to "React", "Amazon Web Services" to "AWS".
                        - EXCLUDE FLUFF: Do not list generic soft skills like "Hard worker" or "Fast learner" unless the resume is devoid of technical skills. Focus on "System Design," "Team Leadership," or "Stakeholder Management" only if supported by evidence.

                        OUTPUT FORMAT RESTRICTIONS:
                        - Return the result as a SINGLE string.
                        - Separated by a tilde character (~).
                        - No labels, no bullet points, no introductory text, no markdown formatting.
                        - Format: Comma-separated Titles ~ Comma-separated Keywords

                        EXAMPLE OUTPUT (Do not copy, use as structure guide):
                        Junior Full Stack Developer, React Engineer, Associate Software Engineer, Frontend Developer, Web Application Developer ~ JavaScript, TypeScript, React, Node.js, Next.js, Redux, PostgreSQL, MongoDB, Docker, AWS, Git, REST APIs, GraphQL, HTML5, CSS3, Tailwind CSS, CI/CD, Agile, Unit Testing, Linux, WebSockets

                        GENERATE OUTPUT NOW:"""
                                    
            #     print(f"Groq ({model}) attempt {attempt+1}/3")
            #     try:
            #         # res = client.models.generate_content(
            #         #         model=model,
            #         #         contents=prompt,
            #         #         config= types.GenerateContentConfig(temperature=0.2)
            #         #         ).text
            #         res = client.chat.completions.create(
            #             messages=[
            #                 {
            #                     "role": "system",
            #                     "content": system_instruction
            #                 },
            #                 {
            #                     "role": "user",
            #                     "content": contents,
            #                 }
            #             ],
            #             model=model,
            #         )
            #         response = res.choices[0].message.content
            #         break
            #     except Exception as e:
            #         print(f"Gemini error: {e}")
            
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                temperature=0.3,
                system_instruction=system_instruction
                )
            ).text
            # print("="*30)
            # print(response)
            # print("="*30)
            [titles,Keywords ]= response.split("~")
            # titles = [title.strip() for title in titles if titles] 
            # print((titles))
            # print(Keywords)
            title_keyword =[]
            title_keyword.append(titles)
            title_keyword.append(Keywords)
            # print(title_keyword[0])
            return title_keyword 

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
    main("https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/1765969051672_SRINIVAS_SAI_SARAN_TEJA.pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS8xNzY1OTY5MDUxNjcyX1NSSU5JVkFTX1NBSV9TQVJBTl9URUpBLnBkZiIsImlhdCI6MTc2NTk2OTA1MSwiZXhwIjoxNzc0NjA5MDUxfQ.OBw39Nt4KNZOeMpTTjAtsOTv_l3-KbGCvhlrEBbz9RA")