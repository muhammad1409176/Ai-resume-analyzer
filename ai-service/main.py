from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
# pyrefly: ignore [missing-import]
import fitz  # PyMuPDF
import os
import tempfile

app = FastAPI()

# ── API Key Authentication ────────────────────────────────────────────────────
API_KEY = os.environ.get("AI_SERVICE_KEY", "dev-internal-key-change-in-production")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

# CORS — restrict to the React dev server in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────────
# Validate uploaded file is a real PDF
# ──────────────────────────────────────────────────────────────────────────────
def validate_pdf(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Read the first 1024 bytes to check for %PDF magic number
    header = file.file.read(1024)
    file.file.seek(0) # Reset file pointer
    if b"%PDF-" not in header:
        raise HTTPException(status_code=400, detail="Invalid PDF file content")

    content_type = file.content_type or ""
    if content_type and "pdf" not in content_type and content_type != "application/octet-stream":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is accepted")


# ──────────────────────────────────────────────────────────────────────────────
# Extract text from PDF using PyMuPDF
# ──────────────────────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────────────────────
# Role-specific keyword categories (improved from single flat list)
# ──────────────────────────────────────────────────────────────────────────────
KEYWORD_CATEGORIES = {
    "languages": ["java", "python", "javascript", "typescript", "go", "rust", "c++", "kotlin", "swift"],
    "frontend":  ["react", "angular", "vue", "html", "css", "sass", "redux", "nextjs"],
    "backend":   ["spring boot", "spring", "fastapi", "django", "node", "express", "rest api"],
    "databases": ["sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch"],
    "devops":    ["docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "git", "github", "jenkins"],
    "practices": ["agile", "scrum", "tdd", "microservices", "api design"],
}

# Required resume sections
REQUIRED_SECTIONS = {
    "skills":     ["skills", "technical skills"],
    "experience": ["experience", "work experience", "employment"],
    "projects":   ["project", "projects", "personal projects"],
    "education":  ["education", "degree", "university", "bachelor", "master"],
}

# Social/professional links
PROFILE_LINKS = {
    "github":   5,
    "linkedin": 5,
}


# ──────────────────────────────────────────────────────────────────────────────
# Analyze text — improved multi-category scoring
# ──────────────────────────────────────────────────────────────────────────────
def analyze_text(text: str) -> dict:
    import re
    # Normalize all whitespace (including \xa0, newlines, tabs) to standard spaces
    normalized_text = re.sub(r'\s+', ' ', text).lower().strip()
    # Apply specific aliases
    lower_text = normalized_text.replace("rest web services", "rest api")

    score = 0
    strengths = []
    missing_keywords = []
    suggestions = []

    # Section checks (up to 40 pts)
    section_found = 0
    for section, keywords in REQUIRED_SECTIONS.items():
        if any(kw in lower_text for kw in keywords):
            section_found += 1
            strengths.append(f"Includes {section} section")
        else:
            suggestions.append(f"Add a {section.capitalize()} section")
    score += section_found * 10  # max 40

    # Profile links (up to 10 pts)
    for link, pts in PROFILE_LINKS.items():
        if link in lower_text:
            score += pts
        else:
            suggestions.append(f"Add your {link.capitalize()} profile link")

    # Category keyword scan (up to 50 pts)
    all_found = []
    all_missing = []
    categories_covered = 0
    for cat, keywords in KEYWORD_CATEGORIES.items():
        found_in_cat = [kw for kw in keywords if kw in lower_text]
        missing_in_cat = [kw for kw in keywords if kw not in lower_text]
        if found_in_cat:
            categories_covered += 1
            all_found.extend(found_in_cat)
        all_missing.extend(missing_in_cat)

    # Award up to 50 pts for breadth of categories covered
    score += min(categories_covered * 9, 50)

    if categories_covered >= 3:
        strengths.append("Strong coverage of multiple technology domains")
    elif categories_covered >= 1:
        strengths.append("Contains relevant technical keywords")

    missing_keywords = all_missing[:10]
    if missing_keywords:
        suggestions.append(
            "Consider adding experience with: " + ", ".join(missing_keywords[:5])
        )

    score = min(score, 100)

    return {
        "score": score,
        "word_count": len(text.split()),
        "strengths": strengths,
        "missing_keywords": missing_keywords,
        "suggestions": suggestions,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Match resume with job description
# ──────────────────────────────────────────────────────────────────────────────
def match_text(resume_text: str, job_description: str) -> dict:
    import re
    # Normalize all whitespace (including \xa0, newlines, tabs) to standard spaces
    resume_lower = re.sub(r'\s+', ' ', resume_text).lower().strip().replace("rest web services", "rest api")
    job_lower = re.sub(r'\s+', ' ', job_description).lower().strip()

    # Flatten all skill keywords for matching
    all_skills = [kw for keywords in KEYWORD_CATEGORIES.values() for kw in keywords]

    matched_keywords = []
    missing_keywords = []

    for skill in all_skills:
        if skill in job_lower:
            if skill in resume_lower:
                matched_keywords.append(skill)
            else:
                missing_keywords.append(skill)

    total_keywords = len(matched_keywords) + len(missing_keywords)
    match_percentage = (
        int((len(matched_keywords) / total_keywords) * 100)
        if total_keywords > 0 else 0
    )

    recommendations = [f"Add experience with {skill}" for skill in missing_keywords[:5]]
    skill_gap_count = len(missing_keywords)
    potential_improvement = min(skill_gap_count * 5, 30)
    priority_skills = missing_keywords[:5]

    # Career path recommendations based on matched skills
    career_recommendations = []
    if "java" in matched_keywords and any(s in matched_keywords for s in ["spring boot", "spring"]):
        career_recommendations.append("Backend Developer")
    if "react" in matched_keywords and "javascript" in matched_keywords:
        career_recommendations.append("Frontend Developer")
    if any(s in matched_keywords for s in ["spring boot", "spring"]) and "react" in matched_keywords:
        career_recommendations.append("Full Stack Developer")
    if "docker" in matched_keywords and any(s in matched_keywords for s in ["aws", "kubernetes", "azure"]):
        career_recommendations.append("DevOps / Cloud Engineer")
    if "python" in matched_keywords and any(s in matched_keywords for s in ["sql", "mysql", "postgresql"]):
        career_recommendations.append("Data Engineer / Analyst")
    if not career_recommendations:
        career_recommendations.append("Software Engineer")

    return {
        "match_percentage": match_percentage,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "recommendations": recommendations,
        "skill_gap_count": skill_gap_count,
        "potential_improvement": potential_improvement,
        "priority_skills": priority_skills,
        "career_recommendations": career_recommendations,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Optimize resume content — smart rewrites
# ──────────────────────────────────────────────────────────────────────────────
def suggest_optimizations(text: str) -> dict:
    import re
    lower_text = text.lower()
    words = text.split()
    
    optimizations = []
    
    # Extract found skills to make suggestions personal
    found_skills = []
    for keywords in KEYWORD_CATEGORIES.values():
        found_skills.extend([kw for kw in keywords if kw in lower_text])
    
    top_skills = list(dict.fromkeys(found_skills))[:3] # Unique top 3
    if not top_skills: top_skills = ["Software Engineering", "System Design"]

    # 1. Professional Summary Context-Aware
    summary_trigger = False
    # If no clear "Summary" or "Profile" section, or if too short
    if not any(kw in lower_text for kw in ["summary", "profile", "objective"]):
        summary_trigger = True
        current_val = "Missing a dedicated Professional Summary section."
    elif len(words) < 300:
        summary_trigger = True
        current_val = "Professional summary is too brief to show impact."
        
    if summary_trigger:
        optimizations.append({
            "category": "Professional Summary",
            "current": current_val,
            "suggestion": f"Accomplished professional with a core focus on {', '.join(top_skills)}. " + 
                          "Expertise in developing scalable applications and driving technical excellence through modern design patterns."
        })

    # 2. Work Experience - Impact vs Responsibility
    impact_keywords = ["achieved", "improved", "increased", "decreased", "reduced", "led", "managed"]
    impact_score = sum(1 for kw in impact_keywords if kw in lower_text)
    
    if "responsible for" in lower_text or impact_score < 3:
        optimizations.append({
            "category": "Experience Impact",
            "current": "Experience section uses passive 'duty-based' language.",
            "suggestion": f"Quantify your achievements using the Google X-Y-Z formula: 'Accomplished [X] as measured by [Y], by doing [Z]'. " + 
                          f"For example: 'Optimized {top_skills[0] if top_skills else 'codebase'} performance by 25% through efficient resource management.'"
        })

    # 3. Technical Skills Breadth
    found_categories = []
    for cat, keywords in KEYWORD_CATEGORIES.items():
        if any(kw in lower_text for kw in keywords):
            found_categories.append(cat)
    
    if len(set(found_categories)) < 3:
        missing_cats = [c for c in KEYWORD_CATEGORIES.keys() if c not in found_categories]
        optimizations.append({
            "category": "Skill Breadth",
            "current": f"Resume is heavily focused on {', '.join(found_categories) if found_categories else 'a few areas'}.",
            "suggestion": f"Broaden your technical profile by highlighting experience in {missing_cats[0] if missing_cats else 'DevOps or Cloud'} technologies " + 
                          "to appear as a more well-rounded candidate."
        })

    return {
        "optimizations": optimizations,
        "overall_tip": "Employers look for 'Impact' over 'Duties'. Ensure every bullet point starts with a strong action verb."
    }


# ──────────────────────────────────────────────────────────────────────────────
# Interview Prep — personalized questions
# ──────────────────────────────────────────────────────────────────────────────
def generate_interview_questions(text: str) -> dict:
    lower_text = text.lower()
    
    # Identify key tech stack to tailor questions
    found_tech = []
    for cat in ['languages', 'frontend', 'backend', 'databases']:
        found_tech.extend([kw for kw in KEYWORD_CATEGORIES.get(cat, []) if kw in lower_text])
    
    tech_context = found_tech[0] if found_tech else "Software Engineering"
    
    questions = [
        {
            "id": 1,
            "type": "Behavioral",
            "question": f"Can you describe a challenging project where you used {tech_context} and how you overcame technical hurdles?",
            "tip": "Focus on the STAR method (Situation, Task, Action, Result)."
        },
        {
            "id": 2,
            "type": "Technical",
            "question": f"What are the core design patterns you follow when building scalable applications with {tech_context}?",
            "tip": "Mention microservices, Clean Architecture, or specific patterns like Singleton/Factory."
        },
        {
            "id": 3,
            "type": "Problem Solving",
            "question": "Imagine our system is experiencing high latency under load. How would you diagnose and optimize it?",
            "tip": "Talk about profiling, indexing, caching, and horizontal scaling."
        },
        {
            "id": 4,
            "type": "Soft Skills",
            "question": "How do you handle disagreements within a technical team regarding architectural decisions?",
            "tip": "Emphasize collaboration, data-driven decisions, and the 'Disagree and Commit' principle."
        },
        {
            "id": 5,
            "type": "Future Focus",
            "question": f"Where do you see the future of {tech_context} heading, and how are you staying ahead of the curve?",
            "tip": "Mention recent updates (e.g., Java 21 features, React 19) and your learning process."
        }
    ]
    
    return {
        "questions": questions,
        "overall_advice": "Research the company's tech stack and prepare specific examples of your impact."
    }


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────
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
async def match_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
):
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
    return {"message": "AI Resume Analyzer API is running"}