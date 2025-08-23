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

# def resumeNotExist(resume_id : str):
#     resume = session.query(ParsedTitle).filter(ParsedTitle.resume_id == resume_id).first()
#     if resume :
        
#         return False
#     else:
#         return True


def main(user, url):

    userID = user
    if userID:
        # UploadedResume = session.query(UploadedResume.file_url,UploadedResume.id).filter(UploadedResume.users_id== userID).first()
            resume_text = (parse_pdf(url))
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite-preview-06-17",
                contents =f"""You are an elite AI hiring strategist and career intelligence specialist with deep expertise in talent acquisition, market trends, and career optimization across the global technology sector.

                    Your mission is to conduct a comprehensive analysis of the provided resume and generate TWO strategically curated outputs that maximize the candidate's market visibility and job matching potential:

                    🎯 **PRIMARY OBJECTIVES:**
                    1. **STRATEGIC JOB TITLES** - Generate 5 solid and quality, high-impact, market-aligned job titles that should align with candidate's skill and expertise spectrum
                    2. **INTELLIGENT KEYWORDS** - Extract 20-25 precisely targeted keywords that create maximum ATS compatibility and recruiter appeal

                    📊 **ADVANCED ANALYSIS FRAMEWORK:**

                    **For JOB TITLES - Apply Multi-Dimensional Matching:**
                    • **Experience Calibration**: Analyze years of experience, project complexity, and leadership indicators to determine accurate seniority levels (Freshers/Entry/Junior/Mid/Senior/Staff/Principal/Architect/VP) make sure to find the best match for the candidate's experience. If the candidate has only projects not having any work experinece he mentioned as fresher or entry level whatever the projects he done he has to mention his professional working experience like company name and duration all stiff orelse he mention only his personal projects he done consider him as fresher or entry level
                    • **Skill Intersection Analysis**: Identify overlapping competencies to suggest hybrid roles (e.g., "Full Stack Engineer", "DevSecOps Specialist", "AI/ML Engineer") dont give the general titles unless the candidate has not worked on any specific domain or technology that may be a personal project or an organization project
                    • **Market Positioning**: Include both traditional titles recruiters search for AND emerging/trendy titles gaining market traction
                    • **Industry Verticals**: Consider domain expertise (FinTech, HealthTech, EdTech, E-commerce, Gaming, etc.) for specialized titles
                    • **Role Evolution Path**: Include both current-level roles AND natural next-step positions for career growth
                    • **Geographical Relevance**: Consider titles popular in target markets (US, Europe, India, etc.)

                    **For KEYWORDS - Execute Comprehensive Extraction:**
                    • **Technical Stack Taxonomy**: Programming languages, frameworks, libraries, databases, cloud platforms, tools, and methodologies
                    • **Domain Intelligence**: Industry-specific terminology, business domains, and vertical expertise
                    • **Soft Skills Mining**: Extract leadership, communication, problem-solving, and collaboration abilities from project descriptions and achievements
                    • **Certification & Standards**: Professional certifications, compliance standards, and industry methodologies
                    • **Emerging Technologies**: AI/ML, blockchain, IoT, edge computing, quantum computing if relevant
                    • **Business Acumen**: Product management, strategy, analytics, and commercial awareness indicators
                    • **Scale & Impact**: Keywords reflecting system scale, user base, performance metrics, and business impact
                    • **Cross-Functional Abilities**: Keywords showing collaboration across teams, stakeholder management, and interdisciplinary skills

                    ⚡ **STRATEGIC ENHANCEMENTS:**
                    • **ATS Optimization**: Prioritize keywords frequently used in job descriptions for target roles
                    • **Recruiter Psychology**: Include terms that trigger recruiter interest and convey seniority/expertise
                    • **Competitive Differentiation**: Highlight unique combinations that set the candidate apart
                    • **Future-Proofing**: Include emerging skills and technologies relevant to career trajectory
                    • **Global Standards**: Use internationally recognized terminology and industry standards

                    🎯 **QUALITY ASSURANCE CRITERIA:**
                    • Job titles must be realistic, specific, and currently in-demand in the market
                    • Keywords must be substantiated by actual resume evidence (no speculation)
                    • Avoid company names, project codenames, or proprietary terminology
                    • Ensure geographic and cultural relevance for target job markets
                    • Balance technical depth with business relevance
                    • Prioritize terms that maximize job matching algorithms

                    📥 **Resume Content for Analysis:**
                    {resume_text}

                    🔥 **ENHANCED OUTPUT REQUIREMENTS:**
                    • **Ranking Logic**: Order titles by market demand + skill alignment + experience match
                    • **Keyword Weighting**: Prioritize by frequency in job descriptions + skill importance + uniqueness factor
                    • **Completeness Check**: Ensure keywords support ALL listed job titles comprehensively
                    • **Market Intelligence**: Reflect current industry trends and hiring patterns

                    ✅ **Precise Output Format:**
                    Return EXCLUSIVELY the analyzed content in this exact structure:

                    Senior Full Stack Engineer, Cloud Solutions Architect, DevOps Engineering Manager, Backend System Engineer, Frontend Technical Lead, Software Engineering Consultant, Platform Engineer, Site Reliability Engineer~JavaScript, TypeScript, React, Node.js, Python, AWS, Kubernetes, Docker, Microservices, GraphQL, PostgreSQL, MongoDB, Redis, Terraform, Jenkins, Git, Agile, Scrum, System Design, API Design, Cloud Architecture, DevOps, CI/CD, Monitoring, Performance Optimization, Team Leadership, Mentoring, Stakeholder Management, Problem Solving, Technical Documentation

                    **Critical**: Maintain the "~" separator and ensure both lists flow from highest to lowest strategic value for the candidate's career positioning."""
                    ,
                config=types.GenerateContentConfig(
                temperature=0.3
                )
            )

            # print(response.text)
            [titles,Keywords ]= response.text.split("~")
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
    main("082a77f6-67f8-4011-bb87-1ae00918da8d","https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/Vamsi_Resume.pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS9WYW1zaV9SZXN1bWUucGRmIiwiaWF0IjoxNzUyNTg1MTA3LCJleHAiOjE3ODQxMjExMDd9.-EGFLMGiF49ttUIlVe99J-50R0vkiJ1aNOUBzD9boUA")