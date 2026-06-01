from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
import fitz  # PyMuPDF
import os
import re
import tempfile
import spacy
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

app = FastAPI()

# ── Load spaCy model ──────────────────────────────────────────────────────────
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# ── API Key Authentication ────────────────────────────────────────────────────
API_KEY = os.environ.get("AI_SERVICE_KEY", "dev-internal-key-change-in-production")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Data ───────────────────────────────────────────────────────────────
KEYWORD_CATEGORIES = {
    "languages":  ["java", "python", "javascript", "typescript", "go", "rust", "c++", "c#", "kotlin", "swift", "php", "ruby", "perl", "r", "dart", "c", "cobol", "fortran", "basic"],
    "frontend":   ["react", "angular", "vue", "html", "css", "sass", "redux", "nextjs", "tailwind", "bootstrap", "jquery", "svelte", "webpack", "babel", "vite"],
    "backend":    ["spring boot", "spring", "fastapi", "django", "node", "express", "rest api", "graphql", "flask", "asp.net", "laravel", "microservices", "grpc", "soap", ".net framework", "com", "corba", "rpc", "win32"],
    "databases":  ["sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb", "oracle", "sqlite", "mariadb", "firebase", "dbase"],
    "cloud_devops":["aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform", "ansible", "ci/cd", "github actions", "gitlab ci", "circleci", "nginx", "helm", "prometheous", "grafana"],
    "mobile":     ["react native", "flutter", "ios", "android", "swiftui", "objective-c"],
    "data_ai":    ["machine learning", "deep learning", "ai", "nlp", "tensorflow", "pytorch", "pandas", "numpy", "matplotlib", "scikit-learn", "opencv", "computer vision", "llm", "genai", "prompt engineering"],
    "testing":    ["jest", "cypress", "selenium", "junit", "mocha", "chai", "playwright", "unit testing", "integration testing"],
    "soft_skills": ["leadership", "collaboration", "agile", "scrum", "project management", "problem solving", "communication", "teamwork", "critical thinking", "mentoring"]
}

REQUIRED_SECTIONS = {
    "skills":     ["skills", "technical skills", "computer skills", "tech stack", "competencies", "strengths", "technical expertise", "packages/methodologies/tools"],
    "experience": ["experience", "work experience", "employment", "professional background", "work history", "career history", "professional experience", "internships", "internship", "trainings", "career summary", "professional summary", "summary"],
    "projects":   ["project", "projects", "personal projects", "academic projects", "key projects", "notable projects"],
    "education":  ["education", "degree", "university", "bachelor", "master", "academic background", "qualifications", "academic credentials", "instruction"],
}

VARIANTS = {
    "spring boot": ["springboot", "spring-boot", "spring framework"],
    "react": ["reactjs", "react.js", "react-js"],
    "rest api": ["restful api", "rest apis", "restful apis", "rest web services", "rest api's"],
    "javascript": ["js", "ecmascript"],
    "typescript": ["ts"],
    "aws": ["amazon web services"],
    "mysql": ["my sql", "mysql database", "mariadb", "lamp"],
    "mongodb": ["mongo db", "mongo", "mern", "mean"],
    "php": ["lamp", "codeigniter", "laravel"],
    "java": ["j2ee", "spring boot", "spring"],
    "c": ["language c", "programming in c"],
}

ACTION_VERBS = ["achieved", "built", "created", "delivered", "designed", "developed", "drove", "engineered", "established", "grew", "implemented", "improved", "increased", "launched", "led", "managed", "optimized", "reduced", "scaled", "shipped", "spearheaded", "streamlined", "analyzed", "planned", "scheduled"]

# ── Utilities ────────────────────────────────────────────────────────────────
def validate_pdf(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    header = file.file.read(1024)
    file.file.seek(0)
    if b"%PDF-" not in header:
        raise HTTPException(status_code=400, detail="Invalid PDF file content")

def extract_text_from_pdf(file_path: str) -> str:
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc: text += page.get_text()
        doc.close()
        return text
    except Exception as e: raise HTTPException(status_code=422, detail=f"Failed to parse PDF: {str(e)}")

def contains_skill(text: str, skill: str) -> bool:
    text_lower = text.lower()
    pattern = rf'\b{re.escape(skill)}\b'
    if re.search(pattern, text_lower): return True
    for v in VARIANTS.get(skill, []):
        if re.search(rf'\b{re.escape(v)}\b', text_lower): return True
    return False

# ── Engines ──────────────────────────────────────────────────────────────────
def analyze_text(text: str) -> dict:
    normalized = re.sub(r'\s+', ' ', text).strip()
    lower = normalized.lower()
    doc = nlp(normalized[:nlp.max_length])

    score = 0
    strengths, suggestions = [], []
    category_counts = Counter()
    found_skills_list = []
    all_found = set()

    # 1. Section Logic
    lines = [L.strip() for L in text.split('\n') if len(L.strip()) > 2]
    for section, keywords in REQUIRED_SECTIONS.items():
        found = False
        for kw in keywords:
            regex = rf'^\s*{re.escape(kw)}[:\s]*(\(.*\))?\s*$'
            if any(re.search(regex, line, re.IGNORECASE) for line in lines):
                found = True; break
        if found:
            strengths.append(f"Includes {section} section")
            score += 8.75
        else:
            suggestions.append(f"Add a dedicated {section.capitalize()} section")

    # 2. Skill Accuracy
    for cat, keywords in KEYWORD_CATEGORIES.items():
        found = [kw for kw in keywords if contains_skill(lower, kw)]
        if found:
            all_found.update(found)
            category_counts[cat] = len(found)
            found_skills_list.extend(found)

    score += min(len(all_found) * 1.5, 35)
    if "github" in lower: score += 5
    if "linkedin" in lower: score += 5

    # 3. Impact
    quantified = len(re.findall(r'\b\d+[\%\+x]?\b|\$[\d,]+[KMB]?', text, re.IGNORECASE))
    score += min((quantified * 4), 20)
    if quantified >= 3: strengths.append(f"{quantified} quantified achievements found")

    return {
        "score": min(round(score, 1), 100),
        "word_count": len(text.split()),
        "strengths": strengths,
        "suggestions": suggestions,
        "nlp_insights": {"persona": dict(category_counts), "quantified": quantified, "found_skills": found_skills_list}
    }

# ── Endpoints ────────────────────────────────────────────────────────────────
@app.post("/analyze", dependencies=[Security(verify_api_key)])
async def endpoint_analyze(file: UploadFile = File(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read()); p = temp.name
    try: return analyze_text(extract_text_from_pdf(p))
    finally:
        if os.path.exists(p): os.remove(p)

@app.post("/match", dependencies=[Security(verify_api_key)])
async def endpoint_match(file: UploadFile = File(...), job_description: str = Form(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read()); p = temp.name
    try:
        res_text = extract_text_from_pdf(p)
        analysis = analyze_text(res_text)
        found = set(analysis["nlp_insights"]["found_skills"])
        job_lower = job_description.lower()
        all_skills = [kw for kws in KEYWORD_CATEGORIES.values() for kw in kws]
        jd_skills = [s for s in all_skills if contains_skill(job_lower, s)]
        matched = [s for s in jd_skills if s in found]
        missing = [s for s in jd_skills if s not in matched]
        pct = int((len(matched)/len(jd_skills))*100) if jd_skills else 0
        return {"match_percentage": pct, "matched_keywords": matched, "missing_keywords": missing, "career_recommendations": ["Software Engineer"]}
    finally:
        if os.path.exists(p): os.remove(p)

@app.post("/interview-prep", dependencies=[Security(verify_api_key)])
async def endpoint_interview(file: UploadFile = File(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read()); p = temp.name
    try:
        analysis = analyze_text(extract_text_from_pdf(p))
        skills = analysis["nlp_insights"]["found_skills"]
        random.shuffle(skills)
        primary = skills[0].capitalize() if skills else "Technical Skills"
        secondary = skills[1].capitalize() if len(skills) > 1 else "Management"
        
        questions = [
            {"id": 1, "type": "Technical", "question": f"Explain the internal architecture of {primary} and how you've used it to solve a complex problem.", "tip": "Focus on high-level efficiency."},
            {"id": 2, "type": "Behavioral", "question": f"Tell me about a time you had to learn {secondary} quickly and apply it to a production environment.", "tip": "Mention your learning speed."}
        ]
        return {"questions": questions, "overall_advice": f"Your strong background in {primary} is a key asset. Focus on impact metrics."}
    finally:
        if os.path.exists(p): os.remove(p)

@app.post("/optimize", dependencies=[Security(verify_api_key)])
async def endpoint_optimize(file: UploadFile = File(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read()); p = temp.name
    try:
        text = extract_text_from_pdf(p)
        analysis = analyze_text(text)
        opts = []
        # Find a sentence without numbers
        sentences = [s.strip() for s in text.split('.') if 20 < len(s.strip()) < 100]
        weak_bullet = random.choice(sentences) if sentences else "Developed various software components."
        
        if analysis["score"] < 80:
            opts.append({"category": "IMPACT", "current": weak_bullet, "suggestion": "Rewrite with metrics: 'Optimized system performance by 30% using efficient algorithms'."})
        if not any(link in text.lower() for link in ["github", "linkedin"]):
            opts.append({"category": "LINKS", "current": "Missing professional branding.", "suggestion": "Add clickable LinkedIn/GitHub links to the header for recruiter visibility."})
        if not opts:
            opts = [{"category": "ELITE", "current": "Strong narrative.", "suggestion": "Consider adding specific cloud deployment metrics (e.g. 99.9% uptime)."}]
            
        return {"optimizations": opts[:2], "overall_tip": "Focus on quantifying your recent role for maximum conversion."}
    finally:
        if os.path.exists(p): os.remove(p)

@app.get("/")
def root(): return {"message": "CareerIQ AI v4.4 - Dynamic Engine"}