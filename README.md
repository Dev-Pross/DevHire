## **Project Overview**

**Problem:**  
 Job seekers waste time tailoring resumes, finding jobs, and applying manually.

**Solution:**  
 Your AI-driven platform automates **end-to-end job application** by:

1. Extracting skills and experience from resumes

2. Searching jobs matching those keywords & experience

3. Generating **ATS-optimized tailored resumes** per job

4. Applying automatically

5. Showing a **dashboard** of applied jobs

---

## **🎯 Key Features – User Flow**

 ✅ **Step 1:** User uploads their resume (PDF/DOCX)  
 ✅ **Step 2:** Resume parser extracts skills, years of experience, roles  
 ✅ **Step 3:** Your app searches jobs (based on extracted keywords \+ experience)  
 ✅ **Step 4:** Lists jobs to the user for selection  
 ✅ **Step 5:** User selects jobs → clicks **Apply**  
 ✅ **Step 6:** For each selected job:

* Generates ATS-optimized resume tailored to **that job description**

* Applies automatically (via web automation or API)  
   ✅ **Step 7:** User sees history of applications with statuses

---

## 

## **🛠️ 1\. Technology Stack**

| Layer | Stack | Why? |
| ----- | ----- | ----- |
| **Frontend** | Next.js \+ Tailwind CSS | Modern, fast UI, reusable components, responsive dashboard |
| **Backend (Core API)** | Node.js (Express) | Handles user auth, orchestrates tasks, connects frontend and services |
| **AI & NLP Microservice** | Python FastAPI | For resume parsing (pdfminer, pyresparser) and powerful NLP |
| **Database** | MongoDB | Stores users, resumes, parsed data, job listings, application history |
| **LLMs** | Together AI / Groq / Hugging Face Inference API | Free APIs for resume rewriting & cover letter generation |
| **Automation** | Selenium (Python) or Puppeteer (Node.js) | Web automation for applying to jobs |
| **Containerization** | Docker \+ Docker Compose | Runs Node \+ Python microservices together with consistent environments |
| **Deployment** | Render.com, Fly.io, or DigitalOcean | Free/cheap scalable deployment |
| **Optional Queue** | Redis Queue (BullMQ) | For managing multiple application tasks asynchronously |

## 

## **⚙️ 2\. System Architecture**

`[User Frontend: React]`  
       `|`  
    `(API calls)`  
       `|`  
`[Backend API: Node.js] <-> [MongoDB]`  
       `|`  
 `Calls Python service via REST`  
       `|`  
`[Python Microservice: FastAPI]`  
       `|`  
`Parses resume & returns skills`  
       `|`  
`[Backend Node.js]`  
       `|`  
 `Searches jobs (scraping or APIs)`  
       `|`  
`Lists jobs to user`  
       `|`  
`User selects jobs & applies`  
       `|`  
`For each selected job:`  
    `- Calls LLM for tailored resume`  
    `- Uses Automation (Selenium/Puppeteer) to apply`  
       `|`  
`Updates application history in MongoDB`

---

## **📝 3\. Detailed Component Responsibilities**

### **🔷 A. Frontend (React.js)**

✅ **Features:**

* File upload for resumes

* Display parsed skills & suggested jobs

* Selection interface for jobs

* Application progress UI

* Application history page

✅ **Packages:**

* `axios` for API calls

* `react-dropzone` or simple input for file uploads

* Tailwind CSS for styling

* Context API or Redux if app state grows

---

### **🔷 B. Backend Core API (Node.js \+ Express)**

✅ **Responsibilities:**

* User authentication (JWT-based)

* File upload endpoint (passes resume to Python service)

* Calls Python FastAPI for parsing

* Calls job search module to scrape/search jobs

* Stores parsed data, job lists, and application history in MongoDB

* Calls LLM APIs for resume rewriting

* Orchestrates job applications (via automation module)

* Exposes REST endpoints to frontend

✅ **Key NPM Packages:**

* `express`, `jsonwebtoken`, `mongoose`, `multer` (file uploads), `axios`, `bullmq` (if using queue)

✅ **Folder Structure Example:**

`/controllers`  
`/routes`  
`/services`  
`/models`

---

### **🔷 C. AI & NLP Microservice (Python FastAPI)**

✅ **Responsibilities:**

* Expose `/parse_resume` endpoint

* Accept uploaded PDF/DOCX from Node.js backend

* Use `pyresparser`, `pdfminer`, `spacy` for parsing

* Return JSON with:

  * Name, email, phone

  * Skills

  * Years of experience

  * Education & roles (if needed)

✅ **Packages:**

* `fastapi`, `uvicorn`, `pdfminer.six`, `pyresparser`, `spacy`, `pydantic`

✅ **Advantages:**  
 Separate microservice ensures Python dependencies do not conflict with Node app and scales independently.

---

### **🔷 D. Database (MongoDB)**

✅ **Collections:**

* **Users:** { \_id, email, password\_hash, name, etc. }

* **Resumes:** { user\_id, original\_file\_path, parsed\_data\_json, uploaded\_at }

* **Jobs:** { job\_id, title, company, skills\_matched, experience\_required, job\_link }

* **Applications:** { user\_id, job\_id, applied\_resume\_file, status, applied\_at }

✅ **Why MongoDB?**  
 Schema flexibility for parsed resumes and jobs.

---

### **🔷 E. Job Search Module**

✅ **How to find jobs?**

1. **Scraping Approach (Most realistic):**

   * Use **Selenium (Python)** or **Puppeteer (Node)** to scrape job listings from:

     * **LinkedIn:** Needs login, complex XPATHs

     * **Indeed:** Easier scraping, less CAPTCHA

     * **Naukri:** Can scrape public listings

2. **API Approach:**

   * **LinkedIn:** No public job search API

   * **Indeed API:** Retired public API, only for partners

   * **Workarounds:** Some third-party unofficial APIs, but scraping is generally used in such projects.

✅ **Implementation Plan:**

* Query \= extracted keywords \+ experience years

* Scrape title, company, location, description, link

* Store in **Jobs collection** in MongoDB

✅ **Filtering Logic:**  
 Calculate match score between resume skills and job description keywords to prioritize listings.

---

### **🔷 F. LLM Integration Module**

✅ **Free LLM APIs to use:**

| Provider | Models | Purpose |
| ----- | ----- | ----- |
| **Together AI** | LLaMA-3.3 70B | Resume rewriting |
| **Groq** | Mistral, LLaMA-3 | Fast summarization & rewriting |
| **Hugging Face Inference API** | T5, BART | Summarization tasks |

✅ **Prompt Example for resume rewriting:**

“Here is the original resume: \[Resume Text\].  
 Here is the job description: \[JD Text\].  
 Rewrite the resume to match the job description and optimize it for ATS with relevant keywords.”

✅ **Returns:** Tailored resume text → convert to PDF → attach to application.

---

### **🔷 G. Automation Module**

✅ **Options:**

1. **Selenium (Python):**

   * Controls browser to fill job application forms

   * Works cross-platform

2. **Puppeteer (Node.js):**

   * Headless Chrome automation

   * More seamless if sticking to JS stack for backend

✅ **Recommended:**  
 If Python service is already used for parsing, using **Selenium (Python)** keeps all automation in that microservice.

✅ **Implementation:**

* For each selected job:

  * Open application page

  * Fill forms with parsed user data

  * Upload **ATS-optimized resume**

  * Submit application

✅ **Limitations:**  
 If sites use CAPTCHA or block bots, manual intervention needed or integrate paid CAPTCHA solvers (future enhancement).

---

### **🔷 H. Deployment Plan**

✅ **Containerization:**

* Dockerize Node.js backend, React frontend, Python FastAPI microservice

✅ **Deployment Options:**

* **Render.com**: Free tier \+ Docker support

* **Fly.io**: Free tier for small containers

* **DigitalOcean droplet**: Cost-effective for combined deployment

✅ **CI/CD:** GitHub Actions for auto build, test, deploy.

---

## **🔑 4\. Project Execution Plan (Milestones)**

| Review tracker |  |  |  |
| :---- | :---- | :---- | :---- |
| **PHASES** | **![Drop-downs][image1] Status** | **Duration** | **To-Do** |
| **Phase 1:** | In progress | **7-July, 2025  \-  14-JULY-2025** | **Research and Documentation** |
| **Phase 2 :** | Not started | **15 \- JULY–2025 27 \- JULY- 2025** | **Backend Dev** |
| **Phase 3:**  | Not started | **28 \- July- 2025 7-Aug \-2025** | **Frontend UI/UX** |
| **Phase 4:**  | Not started | **8 Aug \- 2025 \- 12 Aug 2025**  | **Deployment , Project Live** |

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAQCAYAAAAWGF8bAAAAx0lEQVR4Xu2TYRHCMAyFKwEJSEBCjyVpXIAEHIATJCBhEpCAhEkA0tEtTVcod/zku8ufvDR7fduc+/NTmHkNge6t1QU82x0TQHRMg8i4t7rGI266QJc0b3Xt7Gq1d3jvV69zQyZUn9QAMHg5K8vnpuTBtFNzXzEawj5rKL0AmE7pFku3KXrR8jPHeaRELy00m2NhuYIstT1hPB8OqoF9dKmDbQQD3ZZcTznIJ2S1GmlZ5k4DhENa3FrbDz+Bk5eTIqhVdFbJ8wG0lJX5M/zhmwAAAABJRU5ErkJggg==>
