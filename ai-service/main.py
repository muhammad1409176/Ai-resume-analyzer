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
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine
from sklearn.naive_bayes import MultinomialNB
from collections import Counter
from sentence_transformers import SentenceTransformer, util
import numpy as np

app = FastAPI()

# ── Load spaCy model ──────────────────────────────────────────────────────────
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# ── Load Sentence Transformer (local, no API key) ─────────────────────────────
# Model is cached to ~/.cache/huggingface after first download (~80MB)
print("[AI] Loading sentence-transformers model (all-MiniLM-L6-v2)...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("[AI] Semantic model ready.")

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
    "languages":   ["java", "python", "javascript", "typescript", "go", "rust", "c++", "c#", "kotlin", "swift", "php", "ruby", "perl", "r", "dart", "c", "cobol", "fortran", "basic"],
    "frontend":    ["react", "angular", "vue", "html", "css", "sass", "redux", "nextjs", "tailwind", "bootstrap", "jquery", "svelte", "webpack", "babel", "vite"],
    "backend":     ["spring boot", "spring", "fastapi", "django", "node", "express", "rest api", "graphql", "flask", "asp.net", "laravel", "microservices", "grpc", "soap"],
    "databases":   ["sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb", "oracle", "sqlite", "mariadb", "firebase"],
    "cloud_devops":["aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform", "ansible", "ci/cd", "github actions", "gitlab ci", "nginx", "helm"],
    "mobile":      ["react native", "flutter", "ios", "android", "swiftui", "objective-c"],
    "data_ai":     ["machine learning", "deep learning", "ai", "nlp", "tensorflow", "pytorch", "pandas", "numpy", "matplotlib", "scikit-learn", "opencv", "computer vision", "llm", "genai", "prompt engineering"],
    "testing":     ["jest", "cypress", "selenium", "junit", "mocha", "chai", "playwright", "unit testing", "integration testing"],
    "soft_skills": ["leadership", "collaboration", "agile", "scrum", "project management", "problem solving", "communication", "teamwork", "mentoring"]
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

ACTION_VERBS = [
    "achieved", "built", "created", "delivered", "designed", "developed", "drove", "engineered",
    "established", "grew", "implemented", "improved", "increased", "launched", "led", "managed",
    "optimized", "reduced", "scaled", "shipped", "spearheaded", "streamlined", "analyzed",
    "planned", "scheduled"
]

# ── Role Mapping (skill categories → job roles) ───────────────────────────────
ROLE_MAP = {
    "frontend":    ["Frontend Developer", "UI Engineer", "React Developer"],
    "backend":     ["Backend Developer", "Java Engineer", "API Developer"],
    "data_ai":     ["Data Scientist", "ML Engineer", "AI Researcher"],
    "mobile":      ["Mobile Developer", "Android Developer", "iOS Developer"],
    "cloud_devops":["DevOps Engineer", "Cloud Architect", "Site Reliability Engineer"],
    "databases":   ["Database Administrator", "Data Engineer"],
    "testing":     ["QA Engineer", "Test Automation Engineer"],
    "languages":   ["Software Engineer", "Full Stack Developer"],
    "soft_skills": ["Technical Lead", "Engineering Manager"],
}

# ── Interview question bank per category ──────────────────────────────────────
QUESTION_BANK = {
    "frontend": [
        ("Technical", "Explain the Virtual DOM in {skill} and why it improves performance.", "Draw lifecycle diagrams."),
        ("Technical", "How does {skill} handle state management at scale? Compare with alternatives.", "Mention Redux or Context API if applicable."),
        ("Practical", "Walk me through how you would optimize a slow {skill} application.", "Mention profiling tools and lazy loading."),
    ],
    "backend": [
        ("Technical", "Describe how {skill} handles dependency injection and inversion of control.", "Mention the IoC container pattern."),
        ("Design", "How would you design a rate-limiting middleware in {skill}?", "Think about token bucket vs leaky bucket."),
        ("Practical", "Explain how you've used {skill} to build a RESTful API with proper error handling.", "Mention HTTP status codes and validation."),
    ],
    "data_ai": [
        ("Technical", "Explain the bias-variance tradeoff and how it affects your {skill} models.", "Give a real example from your experience."),
        ("Practical", "How did you handle imbalanced datasets in a {skill} project?", "SMOTE, class weights, or resampling."),
        ("Design", "Walk me through the end-to-end pipeline you'd build for a {skill} deployment.", "Include data prep, training, evaluation, and serving."),
    ],
    "cloud_devops": [
        ("Technical", "How does container orchestration work in {skill}? Explain pods and services.", "Mention health checks and rolling updates."),
        ("Practical", "Walk me through a CI/CD pipeline you've built using {skill}.", "Cover build, test, and deploy stages."),
    ],
    "databases": [
        ("Technical", "Explain ACID properties and how {skill} enforces them.", "Give a real transaction scenario."),
        ("Design", "When would you choose {skill} over a different database paradigm?", "Compare relational vs non-relational tradeoffs."),
    ],
    "mobile": [
        ("Technical", "Explain the component lifecycle in {skill} and how you manage memory.", "Mention foreground/background transitions."),
        ("Practical", "How do you handle offline state and data sync in a {skill} app?", "Think about local caching and conflict resolution."),
    ],
    "testing": [
        ("Practical", "Describe your testing strategy using {skill}. How do you decide what to test?", "Cover unit, integration, and E2E layers."),
    ],
    "languages": [
        ("Technical", "Explain memory management in {skill} — how does GC or ownership work?", "Give an example of a memory leak and how you detected it."),
        ("Behavioral", "Tell me about the most complex algorithm you've implemented in {skill}.", "Discuss time and space complexity."),
    ],
    "soft_skills": [
        ("Behavioral", "Describe a time you applied {skill} to resolve a cross-team conflict.", "Focus on measurable outcomes."),
    ],
    "default": [
        ("Technical", "Explain the internal architecture of {skill} and a complex problem you solved with it.", "Focus on high-level efficiency."),
        ("Behavioral", "Tell me about a time you had to learn {skill} quickly and apply it to production.", "Mention your learning speed and the outcome."),
    ]
}

# ── Build TF-IDF Role Classifier (trained from keyword categories, no API) ────
def _build_role_classifier():
    """Train a lightweight Naive Bayes classifier from keyword category data."""
    corpus, labels = [], []
    for cat, keywords in KEYWORD_CATEGORIES.items():
        roles = ROLE_MAP.get(cat, ["Software Engineer"])
        for role in roles:
            text = " ".join(keywords) + " " + role.lower()
            corpus.append(text)
            labels.append(roles[0])  # primary role per category
    vec = TfidfVectorizer()
    clf = MultinomialNB()
    X = vec.fit_transform(corpus)
    clf.fit(X, labels)
    return vec, clf

_vectorizer, _classifier = _build_role_classifier()

def predict_roles(found_skills: list[str], category_counts: Counter) -> list[str]:
    """Use the TF-IDF classifier + category counts to predict top job roles."""
    if not found_skills:
        return ["Software Engineer"]

    # Classifier prediction
    skills_text = " ".join(found_skills)
    predicted = _classifier.predict(_vectorizer.transform([skills_text]))[0]

    # Also derive roles directly from top categories (more accurate for demos)
    top_cats = [cat for cat, _ in category_counts.most_common(3)]
    direct_roles = []
    for cat in top_cats:
        direct_roles.extend(ROLE_MAP.get(cat, []))

    # Merge and deduplicate, predicted role first
    roles = [predicted] + [r for r in direct_roles if r != predicted]
    return list(dict.fromkeys(roles))[:4]  # max 4 unique roles

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
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse PDF: {str(e)}")

def contains_skill(text: str, skill: str) -> bool:
    text_lower = text.lower()
    pattern = rf'\b{re.escape(skill)}\b'
    if re.search(pattern, text_lower): return True
    for v in VARIANTS.get(skill, []):
        if re.search(rf'\b{re.escape(v)}\b', text_lower): return True
    return False

def extract_entities(text: str) -> dict:
    """Use spaCy NER to extract structured information from resume text."""
    doc = nlp(text[:nlp.max_length])
    companies = list(dict.fromkeys([
        ent.text.strip() for ent in doc.ents
        if ent.label_ == "ORG" and len(ent.text.strip()) > 2
    ]))[:5]
    dates = list(dict.fromkeys([
        ent.text.strip() for ent in doc.ents
        if ent.label_ == "DATE" and len(ent.text.strip()) > 3
    ]))[:6]
    persons = [
        ent.text.strip() for ent in doc.ents
        if ent.label_ == "PERSON" and len(ent.text.strip()) > 3
    ]
    candidate_name = persons[0] if persons else "Candidate"
    return {"name": candidate_name, "companies": companies, "dates": dates}

# ── Core Analysis Engine ──────────────────────────────────────────────────────
def analyze_text(text: str) -> dict:
    normalized = re.sub(r'\s+', ' ', text).strip()
    lower = normalized.lower()
    doc = nlp(normalized[:nlp.max_length])

    score = 0
    strengths, suggestions = [], []
    category_counts = Counter()
    found_skills_list = []
    all_found = set()

    # 1. Section Detection
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

    # 2. Semantic Skill Detection
    for cat, keywords in KEYWORD_CATEGORIES.items():
        found = [kw for kw in keywords if contains_skill(lower, kw)]
        if found:
            all_found.update(found)
            category_counts[cat] = len(found)
            found_skills_list.extend(found)

    score += min(len(all_found) * 1.5, 35)
    if "github" in lower: score += 5
    if "linkedin" in lower: score += 5

    # 3. Quantified Impact Detection
    quantified = len(re.findall(r'\b\d+[\%\+x]?\b|\$[\d,]+[KMB]?', text, re.IGNORECASE))
    score += min((quantified * 4), 20)
    if quantified >= 3: strengths.append(f"{quantified} quantified achievements found")

    # 4. Action Verb Detection
    used_verbs = [v for v in ACTION_VERBS if re.search(rf'\b{v}\b', lower)]
    if len(used_verbs) >= 3:
        strengths.append(f"Strong action verbs used ({', '.join(used_verbs[:3])} ...)")

    # 5. spaCy NER Entities
    entities = extract_entities(text)

    # 6. Predict Roles
    predicted_roles = predict_roles(found_skills_list, category_counts)

    return {
        "score": min(round(score, 1), 100),
        "word_count": len(text.split()),
        "strengths": strengths,
        "suggestions": suggestions,
        "entities": entities,
        "career_recommendations": predicted_roles,
        "nlp_insights": {
            "persona": dict(category_counts),
            "quantified": quantified,
            "found_skills": found_skills_list
        }
    }

# ── Endpoints ────────────────────────────────────────────────────────────────
@app.post("/analyze", dependencies=[Security(verify_api_key)])
async def endpoint_analyze(file: UploadFile = File(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read()); p = temp.name
    try:
        return analyze_text(extract_text_from_pdf(p))
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

        # Keyword-level match
        all_skills = [kw for kws in KEYWORD_CATEGORIES.values() for kw in kws]
        jd_skills = [s for s in all_skills if contains_skill(job_lower, s)]
        matched = [s for s in jd_skills if s in found]
        missing = [s for s in jd_skills if s not in matched]
        keyword_pct = int((len(matched) / len(jd_skills)) * 100) if jd_skills else 0

        # ── Semantic similarity via sentence-transformers (the core upgrade) ──
        res_embedding = embedder.encode(res_text[:3000], convert_to_tensor=True)
        jd_embedding  = embedder.encode(job_description[:2000], convert_to_tensor=True)
        semantic_score = float(util.cos_sim(res_embedding, jd_embedding).item())
        semantic_pct   = round(semantic_score * 100, 1)

        # Blend: 60% semantic, 40% keyword for a balanced, honest score
        blended_pct = round(0.6 * semantic_pct + 0.4 * keyword_pct, 1)

        return {
            "match_percentage":    int(blended_pct),
            "semantic_score":      semantic_pct,
            "keyword_score":       keyword_pct,
            "matched_keywords":    matched,
            "missing_keywords":    missing,
            "career_recommendations": analysis["career_recommendations"],
        }
    finally:
        if os.path.exists(p): os.remove(p)

@app.post("/interview-prep", dependencies=[Security(verify_api_key)])
async def endpoint_interview(file: UploadFile = File(...)):
    validate_pdf(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(await file.read()); p = temp.name
    try:
        analysis = analyze_text(extract_text_from_pdf(p))
        skills  = analysis["nlp_insights"]["found_skills"]
        persona = analysis["nlp_insights"]["persona"]  # {category: count}

        questions = []
        q_id = 1

        # Generate questions from top detected categories
        top_cats = [cat for cat, _ in Counter(persona).most_common(4)]
        for cat in top_cats:
            cat_skills = [s for s in skills if contains_skill(
                " ".join(KEYWORD_CATEGORIES.get(cat, [])), s
            )]
            skill_name = cat_skills[0].capitalize() if cat_skills else cat.replace("_", " ").title()
            bank = QUESTION_BANK.get(cat, QUESTION_BANK["default"])
            for q_type, question_tpl, tip in bank[:2]:  # max 2 per category
                questions.append({
                    "id": q_id,
                    "type": q_type,
                    "question": question_tpl.format(skill=skill_name),
                    "tip": tip
                })
                q_id += 1
            if q_id > 8: break  # cap at 8 questions

        # Fallback if no categories detected
        if not questions:
            questions = [
                {"id": 1, "type": "Technical", "question": "Explain a complex technical problem you solved end-to-end.", "tip": "Quantify the impact."},
                {"id": 2, "type": "Behavioral", "question": "Describe a time you had to learn a new technology under pressure.", "tip": "Mention the outcome."},
            ]

        top_role = analysis["career_recommendations"][0] if analysis["career_recommendations"] else "Software Engineer"
        top_skill = skills[0].capitalize() if skills else "Technical Skills"

        return {
            "questions": questions,
            "overall_advice": f"Your profile best fits '{top_role}'. Emphasise your expertise in {top_skill} with measurable outcomes."
        }
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

        sentences = [s.strip() for s in text.split('.') if 20 < len(s.strip()) < 120]
        # Find weak bullets (no numbers, no action verbs)
        weak_bullets = [
            s for s in sentences
            if not re.search(r'\d', s)
            and not any(v in s.lower() for v in ACTION_VERBS)
        ]
        weak_bullet = random.choice(weak_bullets) if weak_bullets else (sentences[0] if sentences else "Developed various software components.")

        if analysis["score"] < 80:
            opts.append({
                "category": "IMPACT",
                "current":  weak_bullet,
                "suggestion": "Rewrite with metrics: 'Optimized system performance by 30%, reducing API response time from 800ms to 200ms.'"
            })
        if not any(link in text.lower() for link in ["github", "linkedin"]):
            opts.append({
                "category": "LINKS",
                "current":  "Missing professional branding links.",
                "suggestion": "Add clickable LinkedIn and GitHub URLs to your header. Recruiters spend 6s scanning — make them count."
            })
        if len(analysis["nlp_insights"]["found_skills"]) < 8:
            missing_cats = [c for c in KEYWORD_CATEGORIES if c not in analysis["nlp_insights"]["persona"]]
            if missing_cats:
                sample = random.choice(KEYWORD_CATEGORIES[missing_cats[0]])
                opts.append({
                    "category": "SKILLS",
                    "current":  f"Skill category '{missing_cats[0]}' not represented.",
                    "suggestion": f"Add relevant tools like '{sample}' to your Skills section to improve ATS keyword coverage."
                })
        if not opts:
            opts = [{"category": "ELITE", "current": "Strong narrative overall.", "suggestion": "Consider adding specific cloud deployment metrics (e.g., '99.9% uptime on AWS ECS') to reach elite tier."}]

        return {"optimizations": opts[:3], "overall_tip": "Focus on quantifying achievements in your most recent role for maximum recruiter conversion."}
    finally:
        if os.path.exists(p): os.remove(p)

@app.get("/")
def root():
    return {"message": "CareerIQ AI v5.0 — Semantic Engine (sentence-transformers + spaCy NER + sklearn)"}