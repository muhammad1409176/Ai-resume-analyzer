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
    allow_origins=[
        "http://localhost:3000",
        "https://*.onrender.com",
        "https://*.firebaseapp.com",
        "https://*.web.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Validate PDF ──────────────────────────────────────────────────────────────
def validate_pdf(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    header = file.file.read(1024)
    file.file.seek(0)
    if b"%PDF-" not in header:
        raise HTTPException(status_code=400, detail="Invalid PDF file content")


# ── Extract text from PDF ─────────────────────────────────────────────────────
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


# ── Skill taxonomy ────────────────────────────────────────────────────────────
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
    "skills":     ["skills", "technical skills"],
    "experience": ["experience", "work experience", "employment"],
    "projects":   ["project", "projects", "personal projects"],
    "education":  ["education", "degree", "university", "bachelor", "master"],
}

PROFILE_LINKS = {"github": 5, "linkedin": 5}

# Strong action verbs for resume impact
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


# ── NLP Helpers ───────────────────────────────────────────────────────────────
def count_action_verbs(doc) -> int:
    """Count strong action verbs in resume using lemmatization."""
    count = 0
    for token in doc:
        if token.lemma_.lower() in ACTION_VERBS and token.pos_ == "VERB":
            count += 1
    return count


def count_quantified_achievements(text: str) -> int:
    """Count bullet points that contain numbers/percentages — sign of impact."""
    pattern = r'\b\d+[\%\+x]?\b|\$[\d,]+[KMB]?'
    return len(re.findall(pattern, text))


def count_passive_phrases(text: str) -> int:
    lower = text.lower()
    return sum(1 for phrase in PASSIVE_PHRASES if phrase in lower)


# ── Core Analyzer ─────────────────────────────────────────────────────────────
def analyze_text(text: str) -> dict:
    normalized = re.sub(r'\s+', ' ', text).strip()
    lower = normalized.lower().replace("rest web services", "rest api")

    # Run spaCy NLP pipeline
    doc = nlp(normalized[:nlp.max_length])

    score = 0
    strengths = []
    suggestions = []

    # 1. Section Check (30 pts)
    section_found = 0
    for section, keywords in REQUIRED_SECTIONS.items():
        if any(kw in lower for kw in keywords):
            section_found += 1
            strengths.append(f"Includes {section} section")
        else:
            suggestions.append(f"Add a dedicated {section.capitalize()} section")
    score += section_found * 7.5 # Max 30

    # 2. Profile Links (10 pts)
    for link, pts in PROFILE_LINKS.items():
        if link in lower:
            score += pts
        else:
            suggestions.append(f"Add your {link.capitalize()} profile link")

    # 3. Keyword Coverage (40 pts)
    all_found, all_missing = [], []
    categories_covered = 0
    for cat, keywords in KEYWORD_CATEGORIES.items():
        found = [kw for kw in keywords if kw in lower]
        if found:
            categories_covered += 1
            all_found.extend(found)
        all_missing.extend([kw for kw in keywords if kw not in lower])

    score += min(len(set(all_found)) * 1.5, 40) # Real industry breadth
    if categories_covered >= 4:
        strengths.append("Exceptional technical breadth across domains")
    elif categories_covered >= 2:
        strengths.append("Good domain coverage (Backend, Frontend, etc.)")

    # 4. Impact Score via spaCy (30 pts)
    action_count = count_action_verbs(doc)
    quantified = count_quantified_achievements(text)
    passive_count = count_passive_phrases(text)

    impact_score = min((action_count * 3) + (quantified * 5), 30)
    impact_score = max(impact_score - (passive_count * 3), 0)
    score += impact_score

    if action_count >= 5:
        strengths.append(f"Uses {action_count} strong action verbs — great for ATS")
    elif action_count >= 2:
        strengths.append("Some impact-driven language detected")

    if quantified >= 3:
        strengths.append(f"{quantified} quantified achievements found — impressive!")
    elif quantified >= 1:
        strengths.append("Some achievements are quantified with numbers")

    if passive_count > 2:
        suggestions.append(
            f"Replace {passive_count} passive phrases ('responsible for', 'worked on') "
            "with strong action verbs like 'Built', 'Led', 'Engineered'"
        )

    if quantified < 2:
        suggestions.append(
            "Add more quantified achievements (e.g., 'Reduced load time by 40%', "
            "'Led a team of 5 engineers')"
        )

    score = min(score, 100)

    return {
        "score": score,
        "word_count": len(text.split()),
        "strengths": strengths,
        "missing_keywords": all_missing[:10],
        "suggestions": suggestions,
        # NLP insights
        "nlp_insights": {
            "action_verbs_found": action_count,
            "quantified_achievements": quantified,
            "passive_phrases": passive_count,
        }
    }


# ── Job Matcher ───────────────────────────────────────────────────────────────
def match_text(resume_text: str, job_description: str) -> dict:
    # Normalize
    resume_lower = re.sub(r'\s+', ' ', resume_text).lower().replace("rest web services", "rest api")
    job_lower = re.sub(r'\s+', ' ', job_description).lower()

    # Hard keyword matching
    all_skills = [kw for kws in KEYWORD_CATEGORIES.values() for kw in kws]
    matched, missing = [], []
    for skill in all_skills:
        if skill in job_lower:
            (matched if skill in resume_lower else missing).append(skill)

    total = len(matched) + len(missing)
    keyword_match_pct = int((len(matched) / total) * 100) if total > 0 else 0

    # TF-IDF Semantic similarity
    try:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf = vectorizer.fit_transform([resume_lower, job_lower])
        semantic_score = int(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100)
    except Exception:
        semantic_score = keyword_match_pct

    # Blend: 60% keyword match, 40% semantic similarity
    match_percentage = int(keyword_match_pct * 0.6 + semantic_score * 0.4)

    # Career path
    career_recommendations = []
    if "java" in matched and any(s in matched for s in ["spring boot", "spring"]):
        career_recommendations.append("Backend Developer")
    if "react" in matched and "javascript" in matched:
        career_recommendations.append("Frontend Developer")
    if any(s in matched for s in ["spring boot", "spring"]) and "react" in matched:
        career_recommendations.append("Full Stack Developer")
    if "docker" in matched and any(s in matched for s in ["aws", "kubernetes", "azure"]):
        career_recommendations.append("DevOps / Cloud Engineer")
    if "python" in matched and any(s in matched for s in ["sql", "mysql", "postgresql"]):
        career_recommendations.append("Data Engineer / Analyst")
    if not career_recommendations:
        career_recommendations.append("Software Engineer")

    return {
        "match_percentage": match_percentage,
        "keyword_match_pct": keyword_match_pct,
        "semantic_similarity": semantic_score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "career_recommendations": career_recommendations,
    }


# ── Optimizer ─────────────────────────────────────────────────────────────────
def suggest_optimizations(text: str) -> dict:
    lower = text.lower()
    words = text.split()
    doc = nlp(text[:nlp.max_length])

    found_skills = [kw for kws in KEYWORD_CATEGORIES.values() for kw in kws if kw in lower]
    top_skills = list(dict.fromkeys(found_skills))[:3] or ["Software Engineering", "System Design"]

    optimizations = []

    # 1. Professional Summary
    if not any(kw in lower for kw in ["summary", "profile", "objective"]):
        current_val = "Missing a dedicated Professional Summary section."
    elif len(words) < 300:
        current_val = "Professional summary is too brief to show impact."
    else:
        current_val = None

    if current_val:
        optimizations.append({
            "category": "Professional Summary",
            "current": current_val,
            "suggestion": (
                f"Accomplished {top_skills[0]} developer with expertise in "
                f"{', '.join(top_skills)}. Delivered scalable, production-grade "
                "solutions and led cross-functional teams to achieve measurable business impact."
            )
        })

    # 2. Impact Language (using spaCy)
    action_count = count_action_verbs(doc)
    passive_count = count_passive_phrases(text)
    quantified = count_quantified_achievements(text)

    if passive_count > 1 or action_count < 5:
        optimizations.append({
            "category": "Experience Impact",
            "current": f"Found {passive_count} passive phrases and only {action_count} strong action verbs.",
            "suggestion": (
                f"Replace passive language with strong verbs. Example: "
                f"'Responsible for {top_skills[0]} backend' → "
                f"'Engineered {top_skills[0]} microservices, reducing latency by 35%'"
            )
        })

    if quantified < 3:
        optimizations.append({
            "category": "Quantified Achievements",
            "current": f"Only {quantified} data-driven achievements detected.",
            "suggestion": (
                "Add metrics to every experience bullet. Use the Google X-Y-Z formula: "
                "'Accomplished [X] as measured by [Y], by doing [Z]'. "
                "Example: 'Improved API response time by 40% through Redis caching'"
            )
        })

    # 3. Skill Breadth
    found_cats = [cat for cat, kws in KEYWORD_CATEGORIES.items() if any(kw in lower for kw in kws)]
    if len(found_cats) < 3:
        missing_cats = [c for c in KEYWORD_CATEGORIES if c not in found_cats]
        optimizations.append({
            "category": "Skill Breadth",
            "current": f"Strong in: {', '.join(found_cats) or 'limited areas'}.",
            "suggestion": (
                f"Expand profile by adding {missing_cats[0] if missing_cats else 'DevOps'} skills. "
                "Employers value T-shaped professionals: deep in one area, broad in others."
            )
        })

    return {
        "optimizations": optimizations,
        "overall_tip": (
            "Employers scan resumes in 6 seconds. Lead every bullet with a strong action verb "
            "and a measurable outcome. Your top skills should appear in the first 3 lines."
        )
    }


# ── Interview Prep ────────────────────────────────────────────────────────────
def generate_interview_questions(text: str) -> dict:
    lower = text.lower()
    doc = nlp(text[:nlp.max_length])

    # Extract actual entities from resume using spaCy NER
    orgs = list(dict.fromkeys([
        ent.text for ent in doc.ents if ent.label_ in ("ORG", "PRODUCT")
        and len(ent.text) > 2
    ]))[:3]

    found_tech = []
    for cat in ["languages", "frontend", "backend", "databases"]:
        found_tech.extend([kw for kw in KEYWORD_CATEGORIES.get(cat, []) if kw in lower])

    tech_context = found_tech[0] if found_tech else "Software Engineering"
    company_context = orgs[0] if orgs else "your previous role"

    questions = [
        {
            "id": 1,
            "type": "Behavioral",
            "question": (
                f"At {company_context}, tell us about a time you faced a major technical challenge "
                f"while working with {tech_context}. How did you resolve it and what was the impact?"
            ),
            "tip": "Use the STAR method (Situation, Task, Action, Result). Quantify the outcome."
        },
        {
            "id": 2,
            "type": "Technical Deep-Dive",
            "question": (
                f"Walk us through the architecture of a complex system you built using {tech_context}. "
                "What trade-offs did you make and why?"
            ),
            "tip": "Mention design patterns, scalability decisions, and specific technologies used."
        },
        {
            "id": 3,
            "type": "Problem Solving",
            "question": (
                "Our production system just experienced a P0 outage. Walk us through your "
                "incident response process, from detection to resolution."
            ),
            "tip": "Cover monitoring, root cause analysis, rollback strategies, and post-mortems."
        },
        {
            "id": 4,
            "type": "Leadership & Collaboration",
            "question": (
                "Describe a time when you disagreed with a technical decision made by your team lead. "
                "How did you handle it?"
            ),
            "tip": "Show empathy, data-driven thinking, and the 'Disagree and Commit' principle."
        },
        {
            "id": 5,
            "type": "Growth Mindset",
            "question": (
                f"The {tech_context} ecosystem is evolving rapidly. "
                "What recent development excites you most, and how are you applying it?"
            ),
            "tip": "Mention specific versions, features, or industry trends you're following."
        }
    ]

    return {
        "questions": questions,
        "overall_advice": (
            "Research the company's engineering blog and tech stack before the interview. "
            "Prepare a concise 'hero story' for each major project on your resume."
        )
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
        text = extract_text_from_pdf(temp_path)
        return suggest_optimizations(text)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/interview-prep", dependencies=[Security(verify_api_key)])
async def interview_prep(file: UploadFile = File(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read())
        temp_path = temp.name
    try:
        text = extract_text_from_pdf(temp_path)
        return generate_interview_questions(text)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/")
def root():
    return {"message": "CareerIQ AI Service — Powered by spaCy NLP"}