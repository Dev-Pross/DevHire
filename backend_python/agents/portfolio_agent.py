import logging
import os
from pathlib import Path

import fitz
from pdf2image import convert_from_bytes
import pytesseract
import requests
from config import GROQ_API
# from google import genai
# from google.genai import types
from groq import Groq
# ╭── Gemini setup ───────────────────────────────────────────────╮

# if not GOOGLE_API:
#     raise ValueError("Set GOOGLE_API env var")
# client = genai.Client(api_key=GOOGLE_API)
# model = "gemini-2.5-flash-native-audio-dialog" # gemini-2.5-flash-lite
client = Groq(
    api_key=GROQ_API,
)
model="openai/gpt-oss-120b"
SYSTEM_INSTRUCTION = r"""
You are an expert front-end engineer and designer. Generate a COMPLETE, PRODUCTION-READY, RESPONSIVE portfolio page using ONLY pure HTML + CSS (no JavaScript, no Tailwind, no external libraries).

INPUT:
You will receive a Portfolio format called <PFormat>. Use ONLY this format for styling, layout, sections, responsive, colours,  and alignment and fill the user data from another input  
You will receive a JSON object called user_data. Use ONLY this data to fill content.

REQUIREMENTS:

1) OUTPUT FORMAT
- Return a single complete HTML document:
  - Starts with: <!DOCTYPE html><html lang="en"> ... </html>
  - Include a <head> with <meta charset="UTF-8">, <meta name="viewport" content="width=device-width, initial-scale=1.0">, a <title> with the user name + "Portfolio".
  - Include a <style> tag in the <head> with ALL CSS inside it.
- Do NOT use Markdown in the output.
- Do NOT include backticks, explanations, or comments. Only raw HTML.


2) DATA BINDING
Use these exact keys from user_data when present:
- user_data.name
- user_data.title
- user_data.email
- user_data.phone
- user_data.location
- user_data.summary
- user_data.links.github
- user_data.links.linkedin
- user_data.links.portfolio
- user_data.skills  (array of strings or {category, items[]})
- user_data.projects (array of {name, description, tech[], url})
- user_data.education (array of {degree, school, location, start_year, end_year, gpa})
- user_data.languages (array of {name, level})

If a field is missing, simply omit it gracefully without writing “N/A”.

NOW GENERATE THE HTML PAGE USING THE PROVIDED user_data and <PFormat>.

"""

# ╰───────────────────────────────────────────────────────────────╯

# ╭─────────────────────────  COLOUR LOG  ─────────────────────────╮

class _C:
    R = "\33[31m"
    G = "\33[32m"
    Y = "\33[33m"
    C = "\33[36m"
    M = "\33[35m"
    Z = "\33[0m"
_PALETTE = {"DEBUG": _C.C, "INFO": _C.G, "WARNING": _C.Y, "ERROR": _C.R, "CRITICAL": _C.M}
class _Fmt(logging.Formatter):
    def format(self, rec):
        rec.levelname = f"{_PALETTE.get(rec.levelname, _C.Z)}{rec.levelname}{_C.Z}"
        return super().format(rec)
hlr = logging.StreamHandler()
hlr.setFormatter(_Fmt("%(asctime)s | %(levelname)s | %(message)s"))
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), handlers=[hlr])
log = logging.getLogger("portfolio")

# ╰───────────────────────────────────────────────────────────────╯


# ╭─────────────────────────  Templates  ─────────────────────────╮

_TAMPLATE = 0

_SAMPLE0 = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{name}} | Portfolio</title>
  <style>
    :root {
      --bg: #f4f4f5;
      --card: #ffffff;
      --text: #111827;
      --muted: #6b7280;
      --accent: #6366f1;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    a { color: inherit; text-decoration: none; }
    header {
      position: sticky;
      top: 0;
      z-index: 10;
      background: rgba(244,244,245,0.95);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid #e5e7eb;
    }
    .nav {
      max-width: 1100px;
      margin: 0 auto;
      padding: 0.75rem 1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .nav-left {
      font-weight: 600;
      font-size: 1rem;
    }
    .nav-links {
      display: flex;
      gap: 1rem;
      font-size: 0.9rem;
      color: var(--muted);
    }
    .nav-links a:hover {
      color: var(--accent);
    }
    main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 1.5rem 1rem 3rem;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .section-card {
      background: var(--card);
      border-radius: 1rem;
      padding: 1.5rem;
      box-shadow: 0 8px 20px rgba(15,23,42,0.06);
    }
    .hero {
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(0, 1.2fr);
      gap: 1.5rem;
      align-items: center;
    }
    .hero-name {
      font-size: clamp(2rem, 5vw, 2.7rem);
      font-weight: 700;
      margin-bottom: 0.5rem;
    }
    .hero-title {
      font-size: 1.05rem;
      color: var(--muted);
      margin-bottom: 1rem;
    }
    .hero-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      font-size: 0.9rem;
      color: var(--muted);
    }
    .chip {
      padding: 0.3rem 0.75rem;
      border-radius: 999px;
      border: 1px solid #e5e7eb;
      background: #f9fafb;
    }
    .hero-actions {
      margin-top: 1.25rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
    }
    .btn {
      padding: 0.5rem 1rem;
      border-radius: 999px;
      border: 1px solid transparent;
      font-size: 0.9rem;
      cursor: pointer;
      transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
    }
    .btn-primary {
      background: var(--accent);
      color: white;
    }
    .btn-primary:hover {
      background: #4f46e5;
    }
    .btn-outline {
      border-color: #e5e7eb;
      background: white;
      color: var(--muted);
    }
    .btn-outline:hover {
      border-color: var(--accent);
      color: var(--accent);
    }
    .hero-right {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      font-size: 0.9rem;
      color: var(--muted);
    }
    .section-title {
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 0.75rem;
    }
    .section-subtitle {
      font-size: 0.9rem;
      color: var(--muted);
      margin-bottom: 1rem;
    }
    .skills-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 0.75rem;
    }
    .skill-group-title {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--muted);
      margin-bottom: 0.4rem;
    }
    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }
    .pill {
      font-size: 0.75rem;
      padding: 0.2rem 0.6rem;
      border-radius: 999px;
      background: #eef2ff;
      color: #4338ca;
    }
    .projects-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 1rem;
    }
    .project-card {
      border-radius: 0.9rem;
      border: 1px solid #e5e7eb;
      padding: 1rem;
      background: #f9fafb;
    }
    .project-name {
      font-size: 0.98rem;
      font-weight: 600;
      margin-bottom: 0.35rem;
    }
    .project-desc {
      font-size: 0.85rem;
      color: var(--muted);
      margin-bottom: 0.5rem;
    }
    .project-tech {
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
      margin-bottom: 0.6rem;
    }
    .project-link {
      font-size: 0.8rem;
      color: var(--accent);
    }
    .edu-item {
      margin-bottom: 0.8rem;
    }
    .edu-degree {
      font-size: 0.95rem;
      font-weight: 600;
    }
    .edu-meta {
      font-size: 0.8rem;
      color: var(--muted);
    }
    .lang-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    .lang-pill {
      font-size: 0.8rem;
      padding: 0.25rem 0.75rem;
      border-radius: 999px;
      background: #e0f2fe;
      color: #0369a1;
    }
    footer {
      text-align: center;
      font-size: 0.75rem;
      color: var(--muted);
      padding: 1rem 0 2rem;
    }
    @media (max-width: 768px) {
      .nav-links { display: none; }
      .hero { grid-template-columns: minmax(0,1fr); }
    }
  </style>
</head>
<body>
  <header>
    <div class="nav">
      <div class="nav-left">{{shortName}}</div>
      <nav class="nav-links">
        <a href="#about">About</a>
        <a href="#skills">Skills</a>
        <a href="#projects">Projects</a>
        <a href="#education">Education</a>
        <a href="#contact">Contact</a>
      </nav>
    </div>
  </header>

  <main>
    <section id="hero" class="section-card hero">
      <div>
        <h1 class="hero-name">{{name}}</h1>
        <p class="hero-title">{{title}}</p>
        <div class="hero-meta">
          <span class="chip">{{location}}</span>
          <span class="chip">Open to: {{headlineRole}}</span>
        </div>
        <div class="hero-actions">
          <a href="mailto:{{email}}" class="btn btn-primary">Contact Me</a>
          <a href="{{links.github}}" class="btn btn-outline">GitHub</a>
          <a href="{{links.linkedin}}" class="btn btn-outline">LinkedIn</a>
        </div>
      </div>
      <div class="hero-right">
        <div><strong>Email:</strong> {{email}}</div>
        <div><strong>Phone:</strong> {{phone}}</div>
        <div><strong>Portfolio:</strong> <a href="{{links.portfolio}}">{{links.portfolio}}</a></div>
      </div>
    </section>

    <section id="about" class="section-card">
      <h2 class="section-title">About</h2>
      <p class="section-subtitle">{{summary}}</p>
    </section>

    <section id="skills" class="section-card">
      <h2 class="section-title">Skills</h2>
      <div class="skills-grid">
        <!-- Repeat per skills category -->
        <div>
          <div class="skill-group-title">Frontend</div>
          <div class="pill-row">
            <!-- Repeat per item -->
            <span class="pill">React.js</span>
          </div>
        </div>
      </div>
    </section>

    <section id="projects" class="section-card">
      <h2 class="section-title">Projects</h2>
      <div class="projects-grid">
        <!-- Repeat per project -->
        <article class="project-card">
          <h3 class="project-name">{{project.name}}</h3>
          <p class="project-desc">{{project.description}}</p>
          <div class="project-tech">
            <span class="pill">Next.js</span>
          </div>
          <a href="{{project.url}}" class="project-link">View project →</a>
        </article>
      </div>
    </section>

    <section id="education" class="section-card">
      <h2 class="section-title">Education</h2>
      <!-- Repeat per education entry -->
      <div class="edu-item">
        <div class="edu-degree">{{degree}}</div>
        <div class="edu-meta">{{school}} • {{location}} • {{start_year}}–{{end_year}} • {{gpa}}</div>
      </div>
    </section>

    <section id="contact" class="section-card">
      <h2 class="section-title">Languages</h2>
      <div class="lang-row">
        <!-- Repeat per language -->
        <span class="lang-pill">English — Professional</span>
      </div>
    </section>
  </main>

  <footer>
    © {{year}} {{name}}. All rights reserved.
  </footer>
</body>
</html>

"""

_SAMPLE1 = r"""
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{name}} | Portfolio</title>
  <style>
    :root {
      --bg: #020617;
      --bg-soft: #020617;
      --card: #0b1120;
      --accent: #22c55e;
      --text: #e5e7eb;
      --muted: #9ca3af;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      background: radial-gradient(circle at top, #0f172a, #020617 55%);
      color: var(--text);
    }
    main {
      max-width: 1000px;
      margin: 0 auto;
      padding: 1.5rem 1rem 3rem;
    }
    .hero {
      border-radius: 1.5rem;
      padding: 2rem 1.5rem;
      background: radial-gradient(circle at top left, #22c55e1a, #0b1120);
      border: 1px solid #1f2937;
      margin-bottom: 1.5rem;
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(0, 1.3fr);
      gap: 1.5rem;
      align-items: center;
    }
    .hero-name {
      font-size: clamp(2.2rem, 5vw, 2.8rem);
      font-weight: 700;
    }
    .hero-title {
      margin-top: 0.4rem;
      font-size: 1.05rem;
      color: var(--muted);
    }
    .hero-location {
      margin-top: 0.7rem;
      font-size: 0.9rem;
      color: var(--muted);
    }
    .hero-tags {
      margin-top: 0.9rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    .tag {
      font-size: 0.75rem;
      padding: 0.25rem 0.7rem;
      border-radius: 999px;
      background: #16a34a1a;
      color: #bbf7d0;
      border: 1px solid #16a34a4d;
    }
    .hero-links {
      margin-top: 1.1rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.6rem;
      font-size: 0.85rem;
    }
    .hero-links a {
      color: var(--muted);
    }
    .hero-links a:hover {
      color: var(--accent);
    }
    .hero-right {
      font-size: 0.9rem;
      color: var(--muted);
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }
    .body-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.8fr) minmax(0, 1.2fr);
      gap: 1.25rem;
    }
    .section-card {
      border-radius: 1rem;
      padding: 1.2rem 1.1rem;
      background: var(--card);
      border: 1px solid #111827;
    }
    .section-title {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 0.7rem;
    }
    .section-sub {
      font-size: 0.88rem;
      color: var(--muted);
      margin-bottom: 0.8rem;
    }
    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }
    .pill {
      font-size: 0.75rem;
      padding: 0.2rem 0.6rem;
      border-radius: 999px;
      background: #111827;
      color: var(--muted);
    }
    .project {
      margin-bottom: 0.9rem;
    }
    .project-name {
      font-size: 0.95rem;
      font-weight: 600;
      margin-bottom: 0.25rem;
    }
    .project-desc {
      font-size: 0.8rem;
      color: var(--muted);
      margin-bottom: 0.35rem;
    }
    .project-meta {
      font-size: 0.78rem;
      color: var(--muted);
    }
    .project-meta span {
      margin-right: 0.35rem;
    }
    .project-link {
      margin-top: 0.25rem;
      font-size: 0.8rem;
      color: var(--accent);
    }
    .edu-item {
      margin-bottom: 0.7rem;
    }
    .edu-degree {
      font-size: 0.9rem;
      font-weight: 600;
    }
    .edu-meta {
      font-size: 0.78rem;
      color: var(--muted);
    }
    .lang-list {
      font-size: 0.83rem;
      color: var(--muted);
    }
    .lang-list span {
      display: inline-block;
      margin-right: 0.5rem;
      margin-bottom: 0.25rem;
    }
    footer {
      text-align: center;
      font-size: 0.75rem;
      color: var(--muted);
      margin-top: 2rem;
    }
    @media (max-width: 860px) {
      .hero {
        grid-template-columns: minmax(0, 1fr);
      }
      .body-grid {
        grid-template-columns: minmax(0, 1fr);
      }
    }
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <h1 class="hero-name">{{name}}</h1>
        <p class="hero-title">{{title}}</p>
        <p class="hero-location">{{location}}</p>
        <div class="hero-tags">
          <span class="tag">Full Stack</span>
          <span class="tag">AI Engineer</span>
          <span class="tag">Open to {{headlineRole}}</span>
        </div>
        <div class="hero-links">
          <a href="mailto:{{email}}">Email</a> •
          <a href="{{links.github}}">GitHub</a> •
          <a href="{{links.linkedin}}">LinkedIn</a> •
          <a href="{{links.portfolio}}">Portfolio</a>
        </div>
      </div>
      <div class="hero-right">
        <div><strong>About:</strong> {{summary}}</div>
      </div>
    </section>

    <section class="body-grid">
      <div class="section-card">
        <h2 class="section-title">Projects</h2>
        <!-- Repeat per project -->
        <article class="project">
          <h3 class="project-name">{{project.name}}</h3>
          <p class="project-desc">{{project.description}}</p>
          <div class="project-meta">
            <!-- Repeat tech -->
            <span>Next.js</span><span>FastAPI</span>
          </div>
          <a href="{{project.url}}" class="project-link">View project →</a>
        </article>
      </div>

      <div class="section-card">
        <h2 class="section-title">Skills</h2>
        <div class="section-sub">Tech stack overview</div>
        <!-- Repeat per skills category -->
        <div style="margin-bottom:0.6rem;">
          <div style="font-size:0.8rem;font-weight:600;color:var(--muted);margin-bottom:0.25rem;">Frontend</div>
          <div class="pill-row">
            <span class="pill">React</span>
          </div>
        </div>
      </div>
    </section>

    <section class="body-grid" style="margin-top:1.25rem;">
      <div class="section-card">
        <h2 class="section-title">Education</h2>
        <!-- Repeat per education -->
        <div class="edu-item">
          <div class="edu-degree">{{degree}}</div>
          <div class="edu-meta">{{school}} • {{location}} • {{start_year}}–{{end_year}} • {{gpa}}</div>
        </div>
      </div>
      <div class="section-card">
        <h2 class="section-title">Languages</h2>
        <div class="lang-list">
          <!-- Repeat per language -->
          <span>English — Professional</span>
        </div>
      </div>
    </section>

    <footer>
      Built with HTML & CSS • © {{year}} {{name}}
    </footer>
  </main>
</body>
</html>

"""

_SAMPLE2 = r"""
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{name}} | Portfolio</title>
  <style>
    :root {
      --accent: #8b5cf6;
      --accent-soft: #a855f7;
      --text: #f9fafb;
      --muted: #e5e7eb;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      min-height: 100vh;
      color: var(--text);
      background:
        radial-gradient(circle at top left, #8b5cf61a, transparent 55%),
        radial-gradient(circle at bottom right, #0ea5e91a, transparent 55%),
        linear-gradient(135deg, #020617, #111827 55%, #020617);
    }
    .shell {
      max-width: 1080px;
      margin: 1.5rem auto 2.5rem;
      padding: 0 1rem;
    }
    .glass {
      background: rgba(15,23,42,0.75);
      border-radius: 1.5rem;
      border: 1px solid rgba(148,163,184,0.4);
      box-shadow: 0 18px 60px rgba(15,23,42,0.7);
      backdrop-filter: blur(18px);
      padding: 1.8rem 1.6rem 2rem;
    }
    header {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
      margin-bottom: 1.4rem;
    }
    .h-left {
      max-width: 65%;
    }
    .h-name {
      font-size: clamp(2.1rem, 5vw, 2.7rem);
      font-weight: 700;
    }
    .h-title {
      font-size: 1rem;
      color: var(--muted);
      margin-top: 0.35rem;
    }
    .h-meta {
      margin-top: 0.6rem;
      font-size: 0.85rem;
      color: var(--muted);
    }
    .h-chips {
      margin-top: 0.7rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }
    .chip {
      font-size: 0.75rem;
      padding: 0.25rem 0.7rem;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.6);
      background: rgba(15,23,42,0.8);
    }
    .h-right {
      font-size: 0.8rem;
      color: var(--muted);
      text-align: right;
    }
    .h-right a {
      color: var(--muted);
      text-decoration: none;
    }
    .h-right a:hover {
      color: var(--accent-soft);
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1.6fr) minmax(0, 1.1fr);
      gap: 1.2rem;
      margin-top: 1.2rem;
    }
    .card {
      border-radius: 1rem;
      border: 1px solid rgba(148,163,184,0.4);
      background: radial-gradient(circle at top,rgba(148,163,184,0.16),rgba(15,23,42,0.9));
      padding: 1rem 1rem 1.1rem;
    }
    .card-title {
      font-size: 0.95rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: rgba(209,213,219,0.8);
      margin-bottom: 0.55rem;
    }
    .card-body {
      font-size: 0.85rem;
      color: var(--muted);
    }
    .project {
      margin-bottom: 0.75rem;
    }
    .project-name {
      font-size: 0.92rem;
      font-weight: 600;
      color: #f9fafb;
      margin-bottom: 0.15rem;
    }
    .project-desc {
      font-size: 0.8rem;
      margin-bottom: 0.35rem;
    }
    .project-tech {
      font-size: 0.78rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.3rem;
      margin-bottom: 0.2rem;
    }
    .project-tech span {
      padding: 0.1rem 0.55rem;
      border-radius: 999px;
      background: rgba(55,65,81,0.8);
    }
    .project-link {
      font-size: 0.78rem;
      color: var(--accent-soft);
      text-decoration: none;
    }
    .skills-groups {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }
    .skills-label {
      font-size: 0.8rem;
      font-weight: 600;
      margin-bottom: 0.15rem;
      color: rgba(209,213,219,0.85);
    }
    .skills-row {
      font-size: 0.78rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.3rem;
    }
    .skills-row span {
      padding: 0.2rem 0.6rem;
      border-radius: 999px;
      background: rgba(31,41,55,0.9);
    }
    .edu-item {
      margin-bottom: 0.65rem;
      font-size: 0.8rem;
    }
    .edu-degree {
      font-weight: 600;
      color: #f9fafb;
    }
    .edu-meta {
      color: var(--muted);
    }
    .lang-row {
      font-size: 0.8rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }
    .lang-row span {
      padding: 0.25rem 0.7rem;
      border-radius: 999px;
      background: rgba(15,23,42,0.8);
      border: 1px solid rgba(148,163,184,0.7);
    }
    footer {
      margin-top: 1.8rem;
      font-size: 0.75rem;
      color: var(--muted);
      text-align: center;
    }
    @media (max-width: 800px) {
      .h-left {
        max-width: 100%;
      }
      .h-right {
        text-align: left;
      }
      .grid {
        grid-template-columns: minmax(0,1fr);
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="glass">
      <header>
        <div class="h-left">
          <h1 class="h-name">{{name}}</h1>
          <div class="h-title">{{title}}</div>
          <div class="h-meta">{{location}}</div>
          <div class="h-chips">
            <span class="chip">Full Stack</span>
            <span class="chip">AI & Automation</span>
            <span class="chip">Open to {{headlineRole}}</span>
          </div>
        </div>
        <div class="h-right">
          <div>{{email}}</div>
          <div>{{phone}}</div>
          <div>
            <a href="{{links.github}}">GitHub</a> •
            <a href="{{links.linkedin}}">LinkedIn</a>
          </div>
        </div>
      </header>

      <section class="grid">
        <article class="card">
          <h2 class="card-title">About</h2>
          <div class="card-body">
            {{summary}}
          </div>
        </article>
        <article class="card">
          <h2 class="card-title">Skills</h2>
          <div class="card-body skills-groups">
            <!-- Repeat per category -->
            <div>
              <div class="skills-label">Frontend</div>
              <div class="skills-row">
                <span>React</span>
              </div>
            </div>
          </div>
        </article>
      </section>

      <section class="grid" style="margin-top:1rem;">
        <article class="card">
          <h2 class="card-title">Projects</h2>
          <div class="card-body">
            <!-- Repeat per project -->
            <div class="project">
              <div class="project-name">{{project.name}}</div>
              <div class="project-desc">{{project.description}}</div>
              <div class="project-tech">
                <span>Next.js</span>
              </div>
              <a href="{{project.url}}" class="project-link">View project →</a>
            </div>
          </div>
        </article>
        <article class="card">
          <h2 class="card-title">Education & Languages</h2>
          <div class="card-body">
            <!-- Repeat per education -->
            <div class="edu-item">
              <div class="edu-degree">{{degree}}</div>
              <div class="edu-meta">{{school}} • {{location}} • {{start_year}}–{{end_year}} • {{gpa}}</div>
            </div>
            <div class="lang-row">
              <!-- Repeat per language -->
              <span>English — Professional</span>
            </div>
          </div>
        </article>
      </section>

      <footer>
        © {{year}} {{name}} • Built with HTML & CSS
      </footer>
    </div>
  </div>
</body>
</html>

"""

_SAMPLE3 = r"""
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{name}} | Portfolio</title>
  <style>
    :root {
      --bg: #f1f5f9;
      --left: #0f172a;
      --card: #ffffff;
      --accent: #ec4899;
      --text: #0f172a;
      --muted: #6b7280;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .page {
      max-width: 1100px;
      margin: 1.5rem auto;
      padding: 0 1rem 2.5rem;
      display: grid;
      grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.6fr);
      gap: 1.5rem;
    }
    .left {
      background: var(--left);
      color: #e5e7eb;
      border-radius: 1.5rem;
      padding: 1.7rem 1.4rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .avatar {
      width: 72px;
      height: 72px;
      border-radius: 999px;
      background: linear-gradient(135deg,#ec4899,#6366f1);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 2rem;
      font-weight: 600;
      color: white;
      margin-bottom: 0.5rem;
    }
    .name {
      font-size: 1.4rem;
      font-weight: 700;
    }
    .role {
      font-size: 0.9rem;
      color: #9ca3af;
      margin-bottom: 0.5rem;
    }
    .location {
      font-size: 0.85rem;
      color: #9ca3af;
    }
    .left-section-title {
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #9ca3af;
      margin-top: 0.8rem;
      margin-bottom: 0.3rem;
    }
    .left-links {
      font-size: 0.8rem;
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }
    .left-links a {
      color: #e5e7eb;
      text-decoration: none;
    }
    .left-links a:hover {
      color: var(--accent);
    }
    .left-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
      font-size: 0.75rem;
    }
    .left-tag {
      padding: 0.2rem 0.6rem;
      border-radius: 999px;
      background: #111827;
      color: #e5e7eb;
    }
    .right {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .card {
      background: var(--card);
      border-radius: 1.2rem;
      padding: 1.4rem 1.3rem;
      box-shadow: 0 8px 20px rgba(15,23,42,0.05);
    }
    .card-title {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 0.6rem;
    }
    .card-sub {
      font-size: 0.9rem;
      color: var(--muted);
      margin-bottom: 0.7rem;
    }
    .proj-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit,minmax(260px,1fr));
      gap: 0.8rem;
    }
    .proj {
      border-radius: 0.9rem;
      border: 1px solid #e2e8f0;
      padding: 0.8rem 0.9rem;
      background: #f8fafc;
    }
    .proj-name {
      font-size: 0.95rem;
      font-weight: 600;
      margin-bottom: 0.2rem;
    }
    .proj-desc {
      font-size: 0.8rem;
      color: var(--muted);
      margin-bottom: 0.4rem;
    }
    .proj-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.3rem;
      font-size: 0.75rem;
    }
    .proj-tag {
      padding: 0.15rem 0.5rem;
      border-radius: 999px;
      background: #fee2e2;
      color: #b91c1c;
    }
    .proj-link {
      margin-top: 0.35rem;
      font-size: 0.8rem;
      color: var(--accent);
      text-decoration: none;
    }
    .edu-item {
      margin-bottom: 0.7rem;
      font-size: 0.85rem;
    }
    .edu-degree {
      font-weight: 600;
    }
    .edu-meta {
      color: var(--muted);
      font-size: 0.8rem;
    }
    .skills-rows {
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
      font-size: 0.83rem;
    }
    .skills-row-title {
      font-weight: 600;
      color: var(--muted);
      font-size: 0.8rem;
    }
    .skills-row-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.3rem;
    }
    .skills-row-tag {
      padding: 0.2rem 0.6rem;
      border-radius: 999px;
      background: #f1f5f9;
      font-size: 0.78rem;
    }
    .lang-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      font-size: 0.8rem;
    }
    .lang-pill {
      padding: 0.25rem 0.65rem;
      border-radius: 999px;
      background: #e0f2fe;
      color: #0369a1;
    }
    @media (max-width: 860px) {
      .page {
        grid-template-columns: minmax(0,1fr);
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <aside class="left">
      <div>
        <div class="avatar">{{initials}}</div>
        <div class="name">{{name}}</div>
        <div class="role">{{title}}</div>
        <div class="location">{{location}}</div>
      </div>
      <div>
        <div class="left-section-title">Contact</div>
        <div class="left-links">
          <a href="mailto:{{email}}">{{email}}</a>
          <span>{{phone}}</span>
        </div>
      </div>
      <div>
        <div class="left-section-title">Links</div>
        <div class="left-links">
          <a href="{{links.github}}">GitHub</a>
          <a href="{{links.linkedin}}">LinkedIn</a>
          <a href="{{links.portfolio}}">Portfolio</a>
        </div>
      </div>
      <div>
        <div class="left-section-title">Focus</div>
        <div class="left-tags">
          <span class="left-tag">Full Stack</span>
          <span class="left-tag">AI Apps</span>
          <span class="left-tag">Automation</span>
        </div>
      </div>
    </aside>

    <main class="right">
      <section class="card">
        <h2 class="card-title">About</h2>
        <p class="card-sub">{{summary}}</p>
      </section>

      <section class="card">
        <h2 class="card-title">Projects</h2>
        <div class="proj-grid">
          <!-- Repeat per project -->
          <article class="proj">
            <h3 class="proj-name">{{project.name}}</h3>
            <p class="proj-desc">{{project.description}}</p>
            <div class="proj-tags">
              <span class="proj-tag">Next.js</span>
            </div>
            <a href="{{project.url}}" class="proj-link">View project →</a>
          </article>
        </div>
      </section>

      <section class="card">
        <h2 class="card-title">Skills</h2>
        <div class="skills-rows">
          <!-- Repeat per skills category -->
          <div>
            <div class="skills-row-title">Frontend</div>
            <div class="skills-row-tags">
              <span class="skills-row-tag">React</span>
            </div>
          </div>
        </div>
      </section>

      <section class="card">
        <h2 class="card-title">Education & Languages</h2>
        <!-- Repeat per education -->
        <div class="edu-item">
          <div class="edu-degree">{{degree}}</div>
          <div class="edu-meta">{{school}} • {{location}} • {{start_year}}–{{end_year}} • {{gpa}}</div>
        </div>
        <div class="lang-row">
          <!-- Repeat per language -->
          <span class="lang-pill">English — Professional</span>
        </div>
      </section>
    </main>
  </div>
</body>
</html>

"""

_SAMPLE4 = r"""

<!DOCTYPE html><html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Budumuru Srinivas Sai Saran Teja Portfolio</title>
    <style>
        :root {
            --primary-accent: #6366F1;
            --background-dark: #0f172a;
            --card-background: rgba(255, 255, 255, 0.05);
            --card-border: rgba(255, 255, 255, 0.15);
            --text-color-light: #e2e8f0;
            --text-color-dark: #475569;
            --shadow-color: rgba(0, 0, 0, 0.1);
        }

        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 0;
            background-color: var(--background-dark);
            color: var(--text-color-light);
            line-height: 1.6;
            background-image: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            overflow-x: hidden;
        }

        .container {
            display: flex;
            min-height: 100vh;
        }

        .sidebar {
            width: 260px;
            flex-shrink: 0;
            background-color: var(--card-background);
            border-right: 1px solid var(--card-border);
            backdrop-filter: blur(18px);
            padding: 30px;
            position: sticky;
            top: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .sidebar-header {
            text-align: center;
            margin-bottom: 30px;
        }

        .sidebar-header h1 {
            font-size: 1.8em;
            margin-bottom: 5px;
            color: var(--primary-accent);
            word-break: break-word;
        }

        .sidebar-header h2 {
            font-size: 1.1em;
            font-weight: 400;
            color: var(--text-color-light);
            opacity: 0.8;
            word-break: break-word;
        }

        .sidebar-nav ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .sidebar-nav li {
            margin-bottom: 15px;
        }

        .sidebar-nav a {
            color: var(--text-color-light);
            text-decoration: none;
            font-size: 1.1em;
            transition: color 0.3s ease, transform 0.3s ease;
            display: block;
            padding: 8px 0;
            position: relative;
        }

        .sidebar-nav a:hover {
            color: var(--primary-accent);
            transform: translateX(5px);
        }

        .sidebar-nav a::after {
            content: '';
            position: absolute;
            left: 0;
            bottom: 0;
            width: 0;
            height: 2px;
            background-color: var(--primary-accent);
            transition: width 0.3s ease;
        }

        .sidebar-nav a:hover::after {
            width: 100%;
        }

        .sidebar-social {
            margin-top: 30px;
            text-align: center;
        }

        .sidebar-social a {
            color: var(--text-color-light);
            text-decoration: none;
            margin: 0 10px;
            font-size: 1.5em;
            transition: color 0.3s ease;
        }

        .sidebar-social a:hover {
            color: var(--primary-accent);
        }

        .main-content {
            flex-grow: 1;
            padding: 40px;
            overflow-y: auto;
            max-width: calc(100% - 260px);
        }

        .section {
            margin-bottom: 60px;
            background-color: var(--card-background);
            padding: 30px;
            border-radius: 12px;
            border: 1px solid var(--card-border);
            backdrop-filter: blur(18px);
            box-shadow: 0 4px 15px var(--shadow-color);
        }

        .section h2 {
            font-size: 2em;
            color: var(--primary-accent);
            margin-bottom: 20px;
            border-bottom: 2px solid var(--primary-accent);
            padding-bottom: 10px;
            display: inline-block;
        }

        .hero {
            text-align: center;
            padding: 50px 20px;
        }

        .hero h1 {
            font-size: 3.5em;
            margin-bottom: 10px;
            color: var(--primary-accent);
            line-height: 1.2;
        }

        .hero h2 {
            font-size: 1.8em;
            font-weight: 400;
            margin-bottom: 15px;
            color: var(--text-color-light);
            opacity: 0.9;
        }

        .hero p {
            font-size: 1.2em;
            color: var(--text-color-light);
            opacity: 0.8;
            margin-bottom: 30px;
        }

        .contact-chips {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
        }

        .contact-chip {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 1.1em;
            color: var(--text-color-light);
            text-decoration: none;
            transition: background-color 0.3s ease, transform 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .contact-chip:hover {
            background-color: var(--primary-accent);
            transform: translateY(-3px);
        }

        .contact-chip i {
            font-size: 1.2em;
        }

        .skills-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
        }

        .skill-category {
            margin-bottom: 20px;
        }

        .skill-category h3 {
            font-size: 1.5em;
            color: var(--primary-accent);
            margin-bottom: 15px;
            border-bottom: 1px solid var(--primary-accent);
            padding-bottom: 5px;
        }

        .skill-item {
            background-color: rgba(255, 255, 255, 0.08);
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 1em;
            text-align: center;
            color: var(--text-color-light);
            transition: background-color 0.3s ease, transform 0.3s ease;
        }

        .skill-item:hover {
            background-color: var(--primary-accent);
            transform: translateY(-3px);
        }

        .projects-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 30px;
        }

        .project-card {
            background-color: var(--card-background);
            padding: 25px;
            border-radius: 12px;
            border: 1px solid var(--card-border);
            backdrop-filter: blur(18px);
            box-shadow: 0 4px 15px var(--shadow-color);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            display: flex;
            flex-direction: column;
        }

        .project-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 30px var(--shadow-color);
        }

        .project-card h3 {
            font-size: 1.8em;
            color: var(--primary-accent);
            margin-bottom: 10px;
        }

        .project-card p {
            font-size: 1em;
            color: var(--text-color-light);
            opacity: 0.8;
            margin-bottom: 15px;
            flex-grow: 1;
        }

        .project-tech {
            list-style: none;
            padding: 0;
            margin-bottom: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .project-tech li {
            background-color: rgba(99, 102, 241, 0.2);
            color: var(--primary-accent);
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.9em;
        }

        .project-card-footer {
            display: flex;
            justify-content: flex-end;
            margin-top: auto;
        }

        .project-link {
            background-color: var(--primary-accent);
            color: var(--background-dark);
            padding: 10px 20px;
            border-radius: 20px;
            text-decoration: none;
            font-weight: bold;
            transition: background-color 0.3s ease, transform 0.3s ease;
        }

        .project-link:hover {
            background-color: #4f46e5;
            transform: translateY(-3px);
        }

        .education-item {
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px dashed var(--card-border);
        }

        .education-item:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }

        .education-item h3 {
            font-size: 1.5em;
            color: var(--primary-accent);
            margin-bottom: 5px;
        }

        .education-item h4 {
            font-size: 1.2em;
            color: var(--text-color-light);
            opacity: 0.9;
            margin-bottom: 5px;
        }

        .education-item p {
            font-size: 1em;
            color: var(--text-color-light);
            opacity: 0.7;
            margin-bottom: 5px;
        }

        .languages-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 15px;
        }

        .language-item {
            background-color: rgba(255, 255, 255, 0.08);
            padding: 15px 20px;
            border-radius: 20px;
            font-size: 1.1em;
            color: var(--text-color-light);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.3s ease, transform 0.3s ease;
        }

        .language-item:hover {
            background-color: var(--primary-accent);
            transform: translateY(-3px);
        }

        .language-name {
            font-weight: bold;
        }

        .language-level {
            font-size: 0.9em;
            opacity: 0.8;
        }

        /* Mobile Styles */
        @media (max-width: 768px) {
            .container {
                flex-direction: column;
            }

            .sidebar {
                width: 100%;
                height: auto;
                padding: 20px;
                position: relative;
                border-right: none;
                border-bottom: 1px solid var(--card-border);
                border-radius: 0;
                backdrop-filter: blur(10px);
            }

            .sidebar-header {
                margin-bottom: 20px;
            }

            .sidebar-header h1 {
                font-size: 1.8em;
            }

            .sidebar-header h2 {
                font-size: 1em;
            }

            .sidebar-nav ul {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 10px;
            }

            .sidebar-nav li {
                margin-bottom: 0;
            }

            .sidebar-nav a {
                font-size: 1em;
                padding: 5px 10px;
                border-radius: 15px;
                background-color: rgba(255, 255, 255, 0.05);
            }

            .sidebar-nav a:hover {
                transform: none;
                background-color: var(--primary-accent);
            }

            .sidebar-nav a::after {
                display: none;
            }

            .sidebar-social {
                margin-top: 20px;
            }

            .main-content {
                max-width: 100%;
                padding: 20px;
            }

            .section {
                padding: 20px;
            }

            .section h2 {
                font-size: 1.8em;
            }

            .hero h1 {
                font-size: 2.8em;
            }

            .hero h2 {
                font-size: 1.5em;
            }

            .hero p {
                font-size: 1em;
            }

            .contact-chips {
                flex-direction: column;
                align-items: center;
            }

            .contact-chip {
                width: 80%;
                justify-content: center;
            }

            .projects-grid {
                grid-template-columns: 1fr;
            }

            .education-item {
                padding-bottom: 15px;
            }

            .education-item h3 {
                font-size: 1.3em;
            }

            .education-item h4 {
                font-size: 1.1em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <aside class="sidebar">
            <div class="sidebar-header">
                <h1>Budumuru Srinivas Sai Saran Teja</h1>
                <h2>Full-Stack Software Engineer (MERN + AI Engineer)</h2>
            </div>
            <nav class="sidebar-nav">
                <ul>
                    <li><a href="#hero">Home</a></li>
                    <li><a href="#about">About</a></li>
                    <li><a href="#skills">Skills</a></li>
                    <li><a href="#projects">Projects</a></li>
                    <li><a href="#education">Education</a></li>
                    <li><a href="#languages">Languages</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
            </nav>
            <div class="sidebar-social">
                <a href="https://github.com/TejaBudumuru3" target="_blank" aria-label="GitHub"><i class="fab fa-github"></i></a>
                <a href="https://linkedin.com/in/teja-budumuru-15123a292" target="_blank" aria-label="LinkedIn"><i class="fab fa-linkedin"></i></a>
                <a href="https://teja-budumuru.vercel.app" target="_blank" aria-label="Portfolio"><i class="fas fa-briefcase"></i></a>
                <a href="https://x.com/teja_budumuru" target="_blank" aria-label="X"><i class="fab fa-x-twitter"></i></a>
            </div>
        </aside>
        <main class="main-content">
            <section id="hero" class="section hero">
                <h1>Budumuru Srinivas Sai Saran Teja</h1>
                <h2>Full-Stack Software Engineer (MERN + AI Engineer)</h2>
                <p>Visakhapatnam, Andhra Pradesh, India</p>
                <div class="contact-chips">
                    <a href="mailto:tejabudumuru3@gmail.com" class="contact-chip" aria-label="Email">
                        <i class="fas fa-envelope"></i> tejabudumuru3@gmail.com
                    </a>
                    <a href="tel:+917993027519" class="contact-chip" aria-label="Phone">
                        <i class="fas fa-phone"></i> +91 7993027519
                    </a>
                    <span class="contact-chip">
                        <i class="fas fa-briefcase"></i> Open to roles: Full-Stack & AI Engineering
                    </span>
                </div>
            </section>

            <section id="about" class="section">
                <h2>About Me</h2>
                <p>Full-Stack Software Engineer focused on building AI-driven web products using MERN, FastAPI, and modern frontend frameworks. Experienced in designing scalable APIs, automation workflows, and production-ready UIs for job automation and content generation platforms.</p>
            </section>

            <section id="skills" class="section">
                <h2>Skills</h2>
                <div class="skills-grid">
                    <div class="skill-category">
                        <h3>Frontend</h3>
                        <div class="skills-grid">
                            <span class="skill-item">React.js</span>
                            <span class="skill-item">Next.js</span>
                            <span class="skill-item">TypeScript</span>
                            <span class="skill-item">JavaScript (ES6+)</span>
                            <span class="skill-item">HTML5</span>
                            <span class="skill-item">CSS3</span>
                            <span class="skill-item">Tailwind CSS</span>
                            <span class="skill-item">Redux</span>
                            <span class="skill-item">Context API</span>
                        </div>
                    </div>
                    <div class="skill-category">
                        <h3>Backend</h3>
                        <div class="skills-grid">
                            <span class="skill-item">Node.js</span>
                            <span class="skill-item">Express.js</span>
                            <span class="skill-item">Python</span>
                            <span class="skill-item">FastAPI</span>
                            <span class="skill-item">Flask</span>
                            <span class="skill-item">REST API Design</span>
                            <span class="skill-item">Authentication (JWT, OAuth2)</span>
                        </div>
                    </div>
                    <div class="skill-category">
                        <h3>Databases & Storage</h3>
                        <div class="skills-grid">
                            <span class="skill-item">PostgreSQL</span>
                            <span class="skill-item">MongoDB</span>
                            <span class="skill-item">MySQL</span>
                            <span class="skill-item">Supabase</span>
                            <span class="skill-item">Prisma ORM</span>
                            <span class="skill-item">Database Migrations</span>
                        </div>
                    </div>
                    <div class="skill-category">
                        <h3>DevOps & Tools</h3>
                        <div class="skills-grid">
                            <span class="skill-item">Docker</span>
                            <span class="skill-item">Git</span>
                            <span class="skill-item">GitHub</span>
                            <span class="skill-item">Vercel</span>
                            <span class="skill-item">Railway</span>
                            <span class="skill-item">Render</span>
                            <span class="skill-item">CI/CD Pipelines</span>
                        </div>
                    </div>
                    <div class="skill-category">
                        <h3>Automation & Testing</h3>
                        <div class="skills-grid">
                            <span class="skill-item">Playwright</span>
                            <span class="skill-item">API Testing (Postman)</span>
                            <span class="skill-item">pytest</span>
                            <span class="skill-item">Unit & Integration Testing</span>
                        </div>
                    </div>
                    <div class="skill-category">
                        <h3>AI & Cloud</h3>
                        <div class="skills-grid">
                            <span class="skill-item">Gemini API</span>
                            <span class="skill-item">LLM Prompt Engineering</span>
                            <span class="skill-item">Oracle Cloud Infrastructure (OCI)</span>
                            <span class="skill-item">Generative AI Workflows</span>
                        </div>
                    </div>
                </div>
            </section>

            <section id="projects" class="section">
                <h2>Projects</h2>
                <div class="projects-grid">
                    <div class="project-card">
                        <h3>HireHawk – Intelligent Job Automation Platform</h3>
                        <p>AI-powered job application assistant that discovers roles, tailors resumes, and auto-fills job forms end-to-end.</p>
                        <ul class="project-tech">
                            <li>Next.js</li>
                            <li>TypeScript</li>
                            <li>Tailwind CSS</li>
                            <li>FastAPI</li>
                            <li>Python</li>
                            <li>PostgreSQL (Supabase)</li>
                            <li>Playwright</li>
                            <li>Docker</li>
                        </ul>
                        <div class="project-card-footer">
                            <a href="https://dev-hire-znlr.vercel.app" target="_blank" class="project-link">View Project</a>
                        </div>
                    </div>
                    <div class="project-card">
                        <h3>Ainfinity – AI Content Generation SaaS</h3>
                        <p>MERN-based platform that generates optimized posts for LinkedIn and X using LLM prompts and reusable templates.</p>
                        <ul class="project-tech">
                            <li>React.js</li>
                            <li>Node.js</li>
                            <li>Express.js</li>
                            <li>MongoDB</li>
                            <li>JWT Auth</li>
                            <li>Tailwind CSS</li>
                            <li>Redux</li>
                        </ul>
                        <div class="project-card-footer">
                            <a href="https://post-generator-iota.vercel.app" target="_blank" class="project-link">View Project</a>
                        </div>
                    </div>
                    <div class="project-card">
                        <h3>Resume Tailor & Builder</h3>
                        <p>System that parses resumes, matches them to job descriptions, and generates ATS-friendly resumes with LaTeX.</p>
                        <ul class="project-tech">
                            <li>Python</li>
                            <li>FastAPI</li>
                            <li>Gemini API</li>
                            <li>PostgreSQL</li>
                            <li>LaTeX</li>
                        </ul>
                        <div class="project-card-footer">
                            <a href="https://github.com/TejaBudumuru3" target="_blank" class="project-link">View Project</a>
                        </div>
                    </div>
                    <div class="project-card">
                        <h3>Employee Management System</h3>
                        <p>Desktop application for managing employee records, attendance, and salary computation.</p>
                        <ul class="project-tech">
                            <li>Python</li>
                            <li>Tkinter</li>
                            <li>MySQL</li>
                        </ul>
                        <div class="project-card-footer">
                            <!-- No URL provided for this project -->
                        </div>
                    </div>
                </div>
            </section>

            <section id="education" class="section">
                <h2>Education</h2>
                <div class="education-item">
                    <h3>B.Tech in Computer Science and Engineering</h3>
                    <h4>MVGR College of Engineering (A)</h4>
                    <p>Vizianagaram, Andhra Pradesh, India</p>
                    <p>2022 - 2025</p>
                    <p>GPA: 7.48 / 10</p>
                </div>
                <div class="education-item">
                    <h3>Diploma in Computer Engineering</h3>
                    <h4>Government Polytechnic College</h4>
                    <p>Anakapalle, Andhra Pradesh, India</p>
                    <p>2019 - 2022</p>
                    <p>Score: 82.09%</p>
                </div>
                <div class="education-item">
                    <h3>Oracle Cloud Infrastructure 2025 Certified Generative AI Professional</h3>
                    <h4>Oracle University</h4>
                    <p>Online</p>
                    <p>2025</p>
                </div>
            </section>

            <section id="languages" class="section">
                <h2>Languages</h2>
                <div class="languages-grid">
                    <div class="language-item">
                        <span class="language-name">English</span>
                        <span class="language-level">Professional Working Proficiency</span>
                    </div>
                    <div class="language-item">
                        <span class="language-name">Telugu</span>
                        <span class="language-level">Native</span>
                    </div>
                    <div class="language-item">
                        <span class="language-name">Hindi</span>
                        <span class="language-level">Conversational</span>
                    </div>
                </div>
            </section>

            <section id="contact" class="section">
                <h2>Contact</h2>
                <div class="contact-chips">
                    <a href="mailto:tejabudumuru3@gmail.com" class="contact-chip" aria-label="Email">
                        <i class="fas fa-envelope"></i> tejabudumuru3@gmail.com
                    </a>
                    <a href="tel:+917993027519" class="contact-chip" aria-label="Phone">
                        <i class="fas fa-phone"></i> +91 7993027519
                    </a>
                    <a href="https://github.com/TejaBudumuru3" target="_blank" class="contact-chip" aria-label="GitHub">
                        <i class="fab fa-github"></i> GitHub
                    </a>
                    <a href="https://linkedin.com/in/teja-budumuru-15123a292" target="_blank" class="contact-chip" aria-label="LinkedIn">
                        <i class="fab fa-linkedin"></i> LinkedIn
                    </a>
                    <a href="https://teja-budumuru.vercel.app" target="_blank" class="contact-chip" aria-label="Portfolio">
                        <i class="fas fa-briefcase"></i> Personal Website
                    </a>
                </div>
            </section>
        </main>
    </div>

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</body>
</html>
"""

# ╰───────────────────────────────────────────────────────────────╯

# ╭─────────────────────────  Helper  ─────────────────────────╮

def pdf_to_text(r):
    pdf_bytes = r.content

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
                    log.info("data fetched from resume using **tesseract**")
                else:
                    log.warning(f"unable to fetch the text from resume {page_num + 1}")
            else:
                log.error(f"unable to convert the image from byte fallback method failed!")
    log.info("data fetched from resume")


    docs.close()
    return text

def extract_resume_text(url: str):
    try:
        r = requests.get(url=url, timeout=60)
        r.raise_for_status()

        content_type = r.headers.get("Content-Type","").lower()

        if "pdf" in content_type or url.lower.endswith("pdf"):
            return pdf_to_text(r)
        raise ValueError("Unsupported resume format")
    except requests.HTTPError as e:
        log.error(f"invalid url: {e}")

def build_prompt(user_data: str):
    global SYSTEM_INSTRUCTION, _TAMPLATE
    PFormat = ''
    prompt = ""
    if user_data:
        if _TAMPLATE == 0 :
            PFormat = _SAMPLE0
        elif _TAMPLATE == 1:
            PFormat = _SAMPLE1
        elif _TAMPLATE == 2:
            PFormat = _SAMPLE2
        elif _TAMPLATE == 3:
            PFormat = _SAMPLE3
        elif _TAMPLATE == 4:
            PFormat = _SAMPLE4
        else:
            PFormat = _SAMPLE0

        logging.warning(f"{_TAMPLATE} -  template")
        prompt += "Here is the user_data:\n"+ user_data+ "\n Here is the Template called <PFormat>to use:\n <PFormat>\n"+PFormat+"\n</PFormt>"
        # Path('gemini_portfolio_prompt.txt').write_text(prompt, encoding="utf-8")
        return prompt
    raise ValueError("User data not provided")

def gemini_call(user_data: str):
    prompt = build_prompt(user_data)
    for attempt in range(3):
        log.info("Gemini attempt %d/3", attempt+1)
        try:
            # res = client.models.generate_content(
            #         model=model,
            #         contents=prompt,
            #         config= types.GenerateContentConfig(temperature=0.2)
            #         ).text
            res = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "no preamble just give the html + css code without any explainations, your response should start with <!DOCTYPE html> and end with </html>"
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=model,
            )
            log.debug("Gemini preview: %s", res.choices[0].message.content[:300].replace("\n", " ↩ "))
            return res.choices[0].message.content
        except Exception as e:
            log.error(f"Gemini error: {e}")
            
    raise RuntimeError("Gemini failed 3×")

def code_cleaner(res: str):
    clean = res
    if clean.startswith("```html"):
        clean = clean[7:].lstrip()
    if clean.endswith("```"):
        clean = clean[:-3].rstrip()
    return clean

# ╰───────────────────────────────────────────────────────────────╯

# ╭─────────────────────────  Main functions  ─────────────────────────╮

def generate_portfolio_main(template: int, url: str | None = None, user_data: str | None = None):
    _data = ''
    global _TAMPLATE
    log.debug(f"template in agent- {template}")
    if template: 
        _TAMPLATE = template

    if url:
        _data = extract_resume_text(url)
    elif user_data:
        _data = user_data
    else:
        raise ValueError(" No data provided")

    if _data:
        code = gemini_call(_data)
        # Path("portfolio_code.txt").write_text(code_cleaner(code), encoding='utf-8')
        log.info('portfolio generated from server!!')
        return code_cleaner(code)
    else:
        log.debug('something went wrong')


if __name__ == "__main__":
    RESUME_URL = "https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/1766914489015_AISHWARYA%20RESUME.pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS8xNzY2OTE0NDg5MDE1X0FJU0hXQVJZQSBSRVNVTUUucGRmIiwiaWF0IjoxNzY2OTE0NDkxLCJleHAiOjE3NzU1NTQ0OTF9.Uy4f9nrWkpLLWUPy1KPYJWU_8zqWJlnjp2n0hqGMI-E"
    userdata = r"""
    {
  "user_data": {
    "name": "Budumuru Srinivas Sai Saran Teja",
    "title": "Full-Stack Software Engineer (MERN + AI Engineer)",
    "email": "tejabudumuru3@gmail.com",
    "phone": "+91 7993027519",
    "location": "Visakhapatnam, Andhra Pradesh, India",
    "summary": "Full-Stack Software Engineer focused on building AI-driven web products using MERN, FastAPI, and modern frontend frameworks. Experienced in designing scalable APIs, automation workflows, and production-ready UIs for job automation and content generation platforms.",
    "links": {
      "github": "https://github.com/TejaBudumuru3",
      "linkedin": "https://linkedin.com/in/teja-budumuru-15123a292",
      "portfolio": "https://teja-budumuru.vercel.app",
      "x": "https://x.com/teja_budumuru"
    },
    "skills": [
      {
        "category": "Frontend",
        "items": ["React.js", "Next.js", "TypeScript", "JavaScript (ES6+)", "HTML5", "CSS3", "Tailwind CSS", "Redux", "Context API"]
      },
      {
        "category": "Backend",
        "items": ["Node.js", "Express.js", "Python", "FastAPI", "Flask", "REST API Design", "Authentication (JWT, OAuth2)"]
      },
      {
        "category": "Databases & Storage",
        "items": ["PostgreSQL", "MongoDB", "MySQL", "Supabase", "Prisma ORM", "Database Migrations"]
      },
      {
        "category": "DevOps & Tools",
        "items": ["Docker", "Git", "GitHub", "Vercel", "Railway", "Render", "CI/CD Pipelines"]
      },
      {
        "category": "Automation & Testing",
        "items": ["Playwright", "API Testing (Postman)", "pytest", "Unit & Integration Testing"]
      },
      {
        "category": "AI & Cloud",
        "items": ["Gemini API", "LLM Prompt Engineering", "Oracle Cloud Infrastructure (OCI)", "Generative AI Workflows"]
      }
    ],
    "projects": [
      {
        "name": "HireHawk – Intelligent Job Automation Platform",
        "description": "AI-powered job application assistant that discovers roles, tailors resumes, and auto-fills job forms end-to-end.",
        "tech": ["Next.js", "TypeScript", "Tailwind CSS", "FastAPI", "Python", "PostgreSQL (Supabase)", "Playwright", "Docker"],
        "url": "https://dev-hire-znlr.vercel.app"
      },
      {
        "name": "Ainfinity – AI Content Generation SaaS",
        "description": "MERN-based platform that generates optimized posts for LinkedIn and X using LLM prompts and reusable templates.",
        "tech": ["React.js", "Node.js", "Express.js", "MongoDB", "JWT Auth", "Tailwind CSS", "Redux"],
        "url": "https://post-generator-iota.vercel.app"
      },
      {
        "name": "Resume Tailor & Builder",
        "description": "System that parses resumes, matches them to job descriptions, and generates ATS-friendly resumes with LaTeX.",
        "tech": ["Python", "FastAPI", "Gemini API", "PostgreSQL", "LaTeX"],
        "url": "https://github.com/TejaBudumuru3"
      },
      {
        "name": "Employee Management System",
        "description": "Desktop application for managing employee records, attendance, and salary computation.",
        "tech": ["Python", "Tkinter", "MySQL"],
        "url": ""
      }
    ],
    "education": [
      {
        "degree": "B.Tech in Computer Science and Engineering",
        "school": "MVGR College of Engineering (A)",
        "location": "Vizianagaram, Andhra Pradesh, India",
        "start_year": "2022",
        "end_year": "2025",
        "gpa": "7.48 / 10"
      },
      {
        "degree": "Diploma in Computer Engineering",
        "school": "Government Polytechnic College",
        "location": "Anakapalle, Andhra Pradesh, India",
        "start_year": "2019",
        "end_year": "2022",
        "gpa": "82.09%"
      },
      {
        "degree": "Oracle Cloud Infrastructure 2025 Certified Generative AI Professional",
        "school": "Oracle University",
        "location": "Online",
        "start_year": "2025",
        "end_year": "2025",
        "gpa": ""
      }
    ],
    "languages": [
      { "name": "English", "level": "Professional Working Proficiency" },
      { "name": "Telugu", "level": "Native" },
      { "name": "Hindi", "level": "Conversational" }
    ],
    "interests": [
      "Job automation and scraping",
      "Generative AI applications",
      "Workflow automation (n8n)",
      "Cloud deployment and DevOps",
      "Developer tooling and CLIs"
    ]
  }
}

"""
    generate_portfolio_main(url=RESUME_URL, template=0)


