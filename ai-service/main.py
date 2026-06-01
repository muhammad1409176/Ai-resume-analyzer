from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
import fitz  # PyMuPDF
import os
import re
import tempfile
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
    "languages":  ["java", "python", "javascript", "typescript", "go", "rust", "c++", "c#", "kotlin", "swift", "php", "ruby", "perl", "r", "dart"],
    "frontend":   ["react", "angular", "vue", "html", "css", "sass", "redux", "nextjs", "tailwind", "bootstrap", "jquery", "svelte", "webpack", "babel", "vite"],
    "backend":    ["spring boot", "spring", "fastapi", "django", "node", "express", "rest api", "graphql", "flask", "asp.net", "laravel", "microservices", "grpc", "soap"],
    "databases":  ["sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb", "oracle", "sqlite", "mariadb", "firebase"],
    "cloud_devops":["aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform", "ansible", "ci/cd", "github actions", "gitlab ci", "circleci", "nginx", "helm", "prometheous", "grafana"],
    "mobile":     ["react native", "flutter", "ios", "android", "swiftui", "objective-c"],
    "data_ai":    ["machine learning", "deep learning", "ai", "nlp", "tensorflow", "pytorch", "pandas", "numpy", "matplotlib", "scikit-learn", "opencv", "computer vision", "llm", "genai", "prompt engineering"],
    "testing":    ["jest", "cypress", "selenium", "junit", "mocha", "chai", "playwright", "unit testing", "integration testing"],
    "soft_skills": ["leadership", "collaboration", "agile", "scrum", "project management", "problem solving", "communication", "teamwork", "critical thinking", "mentoring"]
}

REQUIRED_SECTIONS = {
    "skills":     ["skills", "technical skills", "tech stack", "competencies", "strengths"],
    "experience": ["experience", "work experience", "employment", "professional background", "work history", "career history", "professional experience"],
    "projects":   ["project", "projects", "personal projects", "academic projects", "key projects"],
    "education":  ["education", "degree", "university", "bachelor", "master", "academic background", "qualifications"],
}

SKILL_VARIANTS = {
    "spring boot": ["springboot", "spring-boot", "spring framework"],
    "react": ["reactjs", "react.js", "react native"],
    "rest api": ["restful api", "rest apis", "restful apis", "rest web services", "rest api's"],
    "javascript": ["js", "ecmascript"],
    "typescript": ["ts"],
    "aws": ["amazon web services"],
    "gcp": ["google cloud platform", "google cloud"],
    "ci/cd": ["cicd", "continuous integration", "continuous deployment"],
    "mysql": ["my sql", "mysql database", "mariadb"],
    "postgresql": ["postgres", "postgre sql"],
    "mongodb": ["mongo db", "mongo"],
    "html": ["html5"],
    "css": ["css3", "sass", "scss"],
    "communication": ["verbal communication", "written communication", "presentation skills"],
}

ACTION_VERBS = [
    "achieved", "built", "created", "delivered", "designed", "developed",
    "drove", "engineered", "established", "grew", "implemented", "improved",
    "increased", "launched", "led", "managed", "optimized", "reduced",
    "scaled", "shipped", "spearheaded", "streamlined"
]

PASSIVE_PHRASES = [
    "responsible for", "worked on", "helped with", "assisted in",
    "involved in", "participated in", "supported"
]

# ── Utility Functions ─────────────────────────────────────────────────────────
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
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse PDF: {str(e)}")

def contains_skill(text: str, skill: str) -> bool:
    text_lower = text.lower()
    if skill in text_lower:
        return True
    for variant in SKILL_VARIANTS.get(skill, []):
        if variant in text_lower:
            return True
    return False

def count_action_verbs(doc) -> int:
    count = 0
    for token in doc:
        if token.lemma_.lower() in ACTION_VERBS and token.pos_ == "VERB":
            count += 1
    return count

def count_quantified_achievements(text: str) -> int:
    pattern = r'\b\d+[\%\+x]?\b|\$[\d,]+[KMB]?'
    return len(re.findall(pattern, text))

def count_passive_phrases(text: str) -> int:
    lower = text.lower()
    return sum(1 for phrase in PASSIVE_PHRASES if phrase in lower)

# ── Core Analysis Engines ─────────────────────────────────────────────────────
def analyze_text(text: str) -> dict:
    normalized = re.sub(r'\s+', ' ', text).strip()
    lower = normalized.lower()

    # Run spaCy NLP pipeline
    doc = nlp(normalized[:nlp.max_length])

    score = 0
    strengths = []
    suggestions = []

    # 1. Section Check (30 pts)
    section_found = 0
    headers = [line.strip().lower() for line in text.split('\n') if len(line.strip()) < 50]
    
    for section, keywords in REQUIRED_SECTIONS.items():
        if any(kw in lower for kw in keywords) or any(any(kw == h for kw in keywords) for h in headers):
            section_found += 1
            strengths.append(f"Includes {section} section")
        else:
            suggestions.append(f"Add a dedicated {section.capitalize()} section")
    score += section_found * 7.5

    # 2. Key Links (10 pts)
    if "github" in lower: score += 5
    else: suggestions.append("Add your GitHub profile link")
    if "linkedin" in lower: score += 5
    else: suggestions.append("Add your LinkedIn profile link")

    # 3. Keyword Coverage (40 pts)
    all_found = []
    categories_covered = 0
    for cat, keywords in KEYWORD_CATEGORIES.items():
        found = [kw for kw in keywords if contains_skill(lower, kw)]
        if found:
            categories_covered += 1
            all_found.extend(found)

    score += min(len(set(all_found)) * 1.5, 40)
    if categories_covered >= 4: strengths.append("Exceptional technical breadth across domains")
    elif categories_covered >= 2: strengths.append("Good domain coverage (Backend, Frontend, etc.)")

    # 4. Impact Score (30 pts)
    action_count = count_action_verbs(doc)
    quantified = count_quantified_achievements(text)
    passive_count = count_passive_phrases(text)

    impact_score = min((action_count * 3) + (quantified * 5), 30)
    impact_score = max(impact_score - (passive_count * 3), 0)
    score += impact_score

    if action_count >= 5: strengths.append(f"Uses {action_count} strong action verbs — great for ATS")
    if quantified >= 3: strengths.append(f"{quantified} quantified achievements found — impressive!")

    return {
        "score": min(score, 100),
        "word_count": len(text.split()),
        "strengths": strengths,
        "missing_keywords": [], # Can populate if needed
        "suggestions": suggestions,
        "nlp_insights": {
            "action_verbs_found": action_count,
            "quantified_achievements": quantified,
            "passive_phrases": passive_count,
        }
    }

def match_text(resume_text: str, job_description: str) -> dict:
    resume_lower = re.sub(r'\s+', ' ', resume_text).lower()
    job_lower = re.sub(r'\s+', ' ', job_description).lower()

    all_skills = [kw for kws in KEYWORD_CATEGORIES.values() for kw in kws]
    matched, missing = [], []
    
    jd_skills = [skill for skill in all_skills if contains_skill(job_lower, skill)]
    for skill in jd_skills:
        if contains_skill(resume_lower, skill): matched.append(skill)
        else: missing.append(skill)

    keyword_match_pct = int((len(matched) / len(jd_skills)) * 100) if jd_skills else 0
    
    try:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf = vectorizer.fit_transform([resume_lower, job_lower])
        semantic_score = int(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100)
    except:
        semantic_score = keyword_match_pct

    match_percentage = int(keyword_match_pct * 0.6 + semantic_score * 0.4)

    return {
        "match_percentage": match_percentage,
        "keyword_match_pct": keyword_match_pct,
        "semantic_similarity": semantic_score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "career_recommendations": ["Software Engineer"] # Generic fallback
    }

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.post("/analyze", dependencies=[Security(verify_api_key)])
async def analyze_resume(file: UploadFile = File(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read())
        temp_path = temp.name
    try:
        text = extract_text_from_pdf(temp_path)
        return analyze_text(text)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/match", dependencies=[Security(verify_api_key)])
async def match_resume(file: UploadFile = File(...), job_description: str = Form(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read())
        temp_path = temp.name
    try:
        resume_text = extract_text_from_pdf(temp_path)
        return match_text(resume_text, job_description)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/optimize", dependencies=[Security(verify_api_key)])
async def optimize_resume(file: UploadFile = File(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read())
        temp_path = temp.name
    try:
        # Simplified optimization stub to save memory
        text = extract_text_from_pdf(temp_path)
        return {"optimizations": [{"category": "General", "current": "Legacy data", "suggestion": "Add more impact verbs"}]}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/")
def root():
    return {"message": "CareerIQ AI Service — Powered by spaCy NLP"}