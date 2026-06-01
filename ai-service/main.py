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
    "backend":    ["spring boot", "spring", "fastapi", "django", "node", "express", "rest api", "graphql", "flask", "asp.net", "laravel", "microservices", "grpc", "soap", ".net framework", "com", "corba", "rpc"],
    "databases":  ["sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb", "oracle", "sqlite", "mariadb", "firebase", "dbase"],
    "cloud_devops":["aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform", "ansible", "ci/cd", "github actions", "gitlab ci", "circleci", "nginx", "helm", "prometheous", "grafana"],
    "mobile":     ["react native", "flutter", "ios", "android", "swiftui", "objective-c"],
    "data_ai":    ["machine learning", "deep learning", "ai", "nlp", "tensorflow", "pytorch", "pandas", "numpy", "matplotlib", "scikit-learn", "opencv", "computer vision", "llm", "genai", "prompt engineering"],
    "testing":    ["jest", "cypress", "selenium", "junit", "mocha", "chai", "playwright", "unit testing", "integration testing"],
    "soft_skills": ["leadership", "collaboration", "agile", "scrum", "project management", "problem solving", "communication", "teamwork", "critical thinking", "mentoring"]
}

REQUIRED_SECTIONS = {
    "skills":     ["skills", "technical skills", "computer skills", "tech stack", "competencies", "strengths", "technical expertise", "packages/methodologies/\ntools"],
    "experience": ["experience", "experience:", "work experience", "employment", "professional background", "work history", "career history", "professional experience", "internships", "internship", "trainings", "career summary", "professional summary", "summary", "experience: (cont.)"],
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
    "gcp": ["google cloud platform", "google cloud"],
    "ci/cd": ["cicd", "continuous integration", "continuous deployment"],
    "mysql": ["my sql", "mysql database", "mariadb", "lamp"],
    "postgresql": ["postgres", "postgre sql"],
    "mongodb": ["mongo db", "mongo", "mern", "mean"],
    "html": ["html5"],
    "css": ["css3", "sass", "scss"],
    "communication": ["verbal communication", "written communication", "presentation skills"],
    "php": ["lamp", "codeigniter", "laravel"],
    "java": ["j2ee", "spring boot", "spring"],
}

ACTION_VERBS = [
    "achieved", "built", "created", "delivered", "designed", "developed",
    "drove", "engineered", "established", "grew", "implemented", "improved",
    "increased", "launched", "led", "managed", "optimized", "reduced",
    "scaled", "shipped", "spearheaded", "streamlined", "analyzed", "planned", "scheduled"
]

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
    for variant in VARIANTS.get(skill, []):
        if variant in text_lower:
            return True
    return False

def count_quantified_achievements(text: str) -> int:
    num_words = ["three", "four", "five", "six", "seven", "eight", "nine", "ten", "twelve", "fifteen", "twenty", "thirty"]
    pattern = r'\b\d+[\%\+x]?\b|\$[\d,]+[KMB]?|' + '|'.join([rf'\b{w}\b' for w in num_words])
    return len(re.findall(pattern, text, re.IGNORECASE))

# ── Engines ──────────────────────────────────────────────────────────────────
def analyze_text(text: str) -> dict:
    normalized = re.sub(r'\s+', ' ', text).strip()
    lower = normalized.lower()
    doc = nlp(normalized[:nlp.max_length])

    score = 0
    strengths, suggestions = [], []
    category_counts = Counter()
    all_found = set()

    # 1. Section Case-Insensitive Regex Detection
    lines = [L.strip() for L in text.split('\n') if len(L.strip()) > 2]
    for section, keywords in REQUIRED_SECTIONS.items():
        found = False
        for kw in keywords:
            regex = rf'^\s*{re.escape(kw)}[:\s]*(\(.*\))?\s*$'
            if any(re.search(regex, line, re.IGNORECASE) for line in lines):
                found = True; break
            if not found and (f"\n{kw.upper()}" in text or f"\n{kw.capitalize()}:" in text):
                found = True; break
        if found:
            strengths.append(f"Includes {section} section")
            score += 8.75
        else:
            suggestions.append(f"Add a dedicated {section.capitalize()} section")

    # 2. Tech Analysis
    for cat, keywords in KEYWORD_CATEGORIES.items():
        found = [kw for kw in keywords if contains_skill(lower, kw)]
        if found:
            all_found.update(found)
            category_counts[cat] = len(found)

    score += min(len(all_found) * 1.5, 35)
    if "github" in lower: score += 5
    else: suggestions.append("Add your GitHub profile link")
    if "linkedin" in lower: score += 5
    else: suggestions.append("Add your LinkedIn profile link")

    # 3. Impact
    action_count = sum(1 for t in doc if t.lemma_.lower() in ACTION_VERBS and t.pos_ == "VERB")
    quantified = count_quantified_achievements(text)
    score += min((action_count * 2) + (quantified * 3), 20)

    if action_count >= 5: strengths.append(f"Uses {action_count} strong action verbs")
    if quantified >= 3: strengths.append(f"{quantified} quantified achievements found")

    # missing keywords for growth areas
    missing = []
    for cat, _ in category_counts.most_common(2):
        missing.extend([kw for kw in KEYWORD_CATEGORIES[cat] if kw not in all_found][:2])
    if not missing: missing = ["AWS", "Docker", "Go", "Kubernetes"]

    return {
        "score": min(round(score, 1), 100),
        "word_count": len(text.split()),
        "strengths": strengths,
        "missing_keywords": list(set(missing)),
        "suggestions": suggestions,
        "nlp_insights": {"persona": dict(category_counts), "quantified": quantified}
    }

# ── Endpoints ────────────────────────────────────────────────────────────────
@app.post("/analyze", dependencies=[Security(verify_api_key)])
async def endpoint_analyze(file: UploadFile = File(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read()); temp_path = temp.name
    try: return analyze_text(extract_text_from_pdf(temp_path))
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.post("/match", dependencies=[Security(verify_api_key)])
async def endpoint_match(file: UploadFile = File(...), job_description: str = Form(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read()); temp_path = temp.name
    try:
        res_text = extract_text_from_pdf(temp_path)
        all_skills = [kw for kws in KEYWORD_CATEGORIES.values() for kw in kws]
        job_lower = job_description.lower()
        res_lower = res_text.lower()
        jd_skills = [s for s in all_skills if contains_skill(job_lower, s)]
        matched = [s for s in jd_skills if contains_skill(res_lower, s)]
        missing = [s for s in jd_skills if s not in matched]
        pct = int((len(matched)/len(jd_skills))*100) if jd_skills else 0
        return {"match_percentage": pct, "matched_keywords": matched, "missing_keywords": missing, "career_recommendations": ["Full Stack Developer"]}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.post("/interview-prep", dependencies=[Security(verify_api_key)])
async def endpoint_interview(file: UploadFile = File(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read()); temp_path = temp.name
    try:
        analysis = analyze_text(extract_text_from_pdf(temp_path))
        persona = analysis["nlp_insights"]["persona"]
        
        main_focus = list(persona.keys())[0] if persona else "behavioral"
        questions = [
            {
                "id": 1,
                "type": "Technical",
                "question": f"Based on your {main_focus} experience, walk me through the most significant technical trade-off you had to make in a project.",
                "tip": "Focus on the 'Why' - mention cost, performance, or time complexity."
            },
            {
                "id": 2,
                "type": "Leadership",
                "question": "Tell me about a time you mentored a junior developer or influenced a project architecture.",
                "tip": "Highlight your communication skills and ability to look at the big picture."
            }
        ]
        return {"questions": questions, "overallAdvice": "Your technical breadth is impressive. Focus on narrative impact."}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.post("/optimize", dependencies=[Security(verify_api_key)])
async def endpoint_optimize(file: UploadFile = File(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read()); temp_path = temp.name
    try:
        res_text = extract_text_from_pdf(temp_path)
        analysis = analyze_text(res_text)
        opts = []
        
        if analysis["score"] < 80:
            opts.append({
                "category": "PRECISION",
                "current": "Legacy resume formatting with dense text blocks.",
                "suggestion": "Your resume is excellent, but consider customizing keywords for each specific job application to hit 100%."
            })
        if analysis["nlp_insights"]["quantified"] < 10:
            opts.append({
                "category": "IMPACT",
                "current": "Generic project descriptions missing high-level data.",
                "suggestion": "Quantify your achievements: 'Managed a team of 12+' or 'Saved $1million in cost'."
            })
            
        if not opts:
            opts = [{"category": "POLISH", "current": "Strong profile foundation.", "suggestion": "Add more niche technical certifications to the header."}]

        return {"optimizations": opts[:2], "overallTip": "Standardize your section headers for 100% ATS compatibility."}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.get("/")
def root(): return {"message": "CareerIQ AI v4.1 - UI Aligned"}