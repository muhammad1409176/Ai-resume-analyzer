from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
import fitz  # PyMuPDF
import re
from collections import Counter

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Extract text from PDF
# -----------------------------
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


# -----------------------------
# Resume Analysis Endpoint
# -----------------------------
@app.get("/analyze")
def analyze_resume(file_path: str):
    text = extract_text_from_pdf(file_path)
    lower_text = text.lower()

    score = 0
    strengths = []
    missing_keywords = []
    suggestions = []

    # Check for common resume sections
    if "skills" in lower_text or "technical skills" in lower_text:
        score += 20
        strengths.append("Includes technical skills section")
    else:
        suggestions.append("Add a dedicated Skills section")
    if "experience" in lower_text:
        score += 20
        strengths.append("Includes work experience")
    else:
        suggestions.append("Add work experience section")

    if "project" in lower_text or "projects" in lower_text:
        score += 20
        strengths.append("Includes project experience")
    else:
        suggestions.append("Add project section")

    if "github" in lower_text:
        score += 10
    else:
        suggestions.append("Add your GitHub profile link")

    if "linkedin" in lower_text:
        score += 10
    else:
        suggestions.append("Add your LinkedIn profile link")

    # Important technical keywords
    technical_keywords = [
        "java", "python", "react", "spring boot",
        "sql", "mysql", "docker", "aws",
        "javascript", "html", "css"
    ]

    found_keywords = [kw for kw in technical_keywords if kw in lower_text]
    missing_keywords = [kw for kw in technical_keywords if kw not in lower_text]

    score += min(len(found_keywords) * 5, 40)

    if found_keywords:
        strengths.append("Contains many relevant technical keywords")

    if missing_keywords:
        suggestions.append(
            "Include relevant technologies such as: "
            + ", ".join(missing_keywords[:5])
        )

    score = min(score, 100)

    return {
        "score": score,
        "word_count": len(text.split()),
        "strengths": strengths,
        "missing_keywords": missing_keywords,
        "suggestions": suggestions,
    }


# -----------------------------
# Job Matching Endpoint
# -----------------------------
@app.get("/match")
def match_resume(file_path: str, job_description: str):
    resume_text = extract_text_from_pdf(file_path).lower()
    resume_text = resume_text.replace("rest web services", "rest api")
    job_text = job_description.lower()

    # Extract only technical keywords
    skill_keywords = [
        "java", "python", "react", "spring", "spring boot",
        "javascript", "html", "css", "sql", "mysql",
        "docker", "aws", "git", "github", "rest api"
    ]

    matched_keywords = []
    missing_keywords = []

    for skill in skill_keywords:
        if skill in job_text:
            if skill in resume_text:
                matched_keywords.append(skill)
            else:
                missing_keywords.append(skill)

    total_keywords = len(matched_keywords) + len(missing_keywords)

    if total_keywords == 0:
        match_percentage = 0
    else:
        match_percentage = int((len(matched_keywords) / total_keywords) * 100)
    recommendations = [
        f"Add experience with {skill}"
        for skill in missing_keywords[:5]
    ]

    skill_gap_count = len(missing_keywords)
    potential_improvement = min(skill_gap_count * 5, 25)
    priority_skills = missing_keywords[:5]
    career_recommendations = []

    if "java" in matched_keywords and ("spring" in matched_keywords or "spring boot" in matched_keywords):
        career_recommendations.append("Backend Developer")

    if "react" in matched_keywords and "javascript" in matched_keywords:
        career_recommendations.append("Frontend Developer")

    if "java" in matched_keywords and "react" in matched_keywords:
        career_recommendations.append("Full Stack Developer")

    if "docker" in matched_keywords and "aws" in matched_keywords:
        career_recommendations.append("DevOps Engineer")

    if "python" in matched_keywords and "sql" in matched_keywords:
        career_recommendations.append("Data Analyst")

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
      "career_recommendations": career_recommendations
    }