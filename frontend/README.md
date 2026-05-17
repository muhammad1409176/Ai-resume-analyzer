# AI Resume Analyzer

A full-stack AI-powered web application that automates resume screening, ATS scoring, job description matching, skills gap analysis, career recommendations, and PDF report generation.

---

## 📌 Project Overview

AI Resume Analyzer helps placement officers and recruiters quickly evaluate resumes for software engineering roles.

The system:

* Extracts text from uploaded PDF resumes
* Calculates an ATS (Applicant Tracking System) score
* Matches resumes against job descriptions
* Identifies missing technical skills
* Recommends career roles
* Redirects users to relevant LinkedIn job searches
* Generates downloadable PDF reports
* Displays analytics dashboards with charts

---

## 🎯 Problem Statement

Manual resume screening is time-consuming and inconsistent.

This project automates the process by using AI and keyword-based analysis to:

* Improve hiring efficiency
* Identify qualified candidates faster
* Highlight skill gaps
* Suggest relevant career opportunities

---

## ✨ Key Features

### 🔐 Admin Authentication

* Secure admin login
* Session persistence using localStorage
* Logout functionality

### 📄 Resume Upload & Analysis

* Upload PDF resumes
* Extract resume text using PyMuPDF
* Generate ATS score (0–100)
* Detect strengths and weaknesses
* Suggest improvements

### 📝 Job Description Matching

* Compare resume with job description
* Calculate match percentage
* Show matched and missing keywords

### 📊 Skills Gap Analysis

* Count missing skills
* Estimate potential score improvement
* Highlight priority skills to learn

### 🚀 Career Recommendations

* Suggest software roles based on skills
* Open LinkedIn Jobs search directly

### 📑 PDF Report Generation

* Download complete analysis report

### 📈 Analytics Dashboard

* ATS score distribution
* Top missing skills
* Recommended roles
* Monthly trend charts

### 🛠️ Admin Dashboard

* Total resumes analyzed
* Average ATS score
* Highest score
* Most missing skill
* Most recommended role

---

## 🏗️ System Architecture

```text
React Frontend
      ↓
Spring Boot REST API
      ↓
Python FastAPI AI Service
      ↓
MySQL Database
```

---

## 🧰 Technology Stack

### Frontend

* React.js
* Axios
* Recharts
* CSS3

### Backend

* Java 17+
* Spring Boot
* Spring Data JPA
* Maven

### AI Service

* Python
* FastAPI
* PyMuPDF (fitz)
* Uvicorn

### Database

* MySQL

### Report Generation

* PDF generation service

---

## 📂 Project Structure

```text
resume-analyser/
├── frontend/          # React application
├── backend/           # Spring Boot application
├── ai-service/        # Python FastAPI service
├── uploads/           # Uploaded resumes
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd resume-analyser
```

### 2. Configure MySQL

Create a database:

```sql
CREATE DATABASE resume_analyzer;
```

Update `backend/src/main/resources/application.properties`:

```properties
spring.datasource.url=jdbc:mysql://localhost:3306/resume_analyzer
spring.datasource.username=root
spring.datasource.password=your_password
spring.jpa.hibernate.ddl-auto=update
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
npm install axios recharts
```

### 4. Install Python Dependencies

```bash
cd ../ai-service
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn pymupdf
```

---

## ▶️ Running the Project

### Start Python AI Service

```bash
cd ai-service
venv\Scripts\activate
python -m uvicorn main:app --reload --port 8000
```

### Start Spring Boot Backend

```bash
cd backend
mvn spring-boot:run
```

### Start React Frontend

```bash
cd frontend
npm start
```

### Open Application

```text
http://localhost:3000
```

---

## 🔑 Admin Credentials

```text
Username: admin
Password: admin123
```

---

## 🔌 API Endpoints

### Spring Boot APIs

| Method | Endpoint                          | Description                       |
| -----: | --------------------------------- | --------------------------------- |
|   POST | `/api/resumes/upload-and-analyze` | Upload and analyze resume         |
|   POST | `/api/resumes/match-job`          | Match resume with job description |
|   POST | `/api/resumes/generate-report`    | Generate PDF report               |
|    GET | `/api/admin/stats`                | Fetch admin dashboard statistics  |

### Python FastAPI APIs

| Method | Endpoint   | Description                          |
| -----: | ---------- | ------------------------------------ |
|    GET | `/analyze` | Analyze resume text                  |
|    GET | `/match`   | Match resume against job description |

---

## 📊 ATS Scoring Criteria

The system evaluates:

* Skills section
* Work experience
* Projects
* GitHub profile
* LinkedIn profile
* Technical keywords

Typical score ranges:

* 0–40: Poor
* 41–60: Average
* 61–80: Good
* 81–100: Excellent

---

## 👨‍💼 How Placement Officers Use This System

1. Login as admin
2. Upload student resume
3. Analyze ATS score
4. Paste job description
5. View match percentage
6. Identify missing skills
7. Explore recommended roles on LinkedIn
8. Download PDF report
9. Monitor analytics dashboard

---

## 📈 Analytics Charts

The dashboard includes:

* ATS Score Distribution
* Top Missing Skills
* Recommended Roles
* Monthly Trends

> Note: Current charts use sample data to demonstrate visualization. In production, these can be connected to live database statistics.

---

## 🔮 Future Enhancements

* Real-time chart data from database
* Candidate login portal
* Email notifications
* OCR support for scanned resumes
* NLP-based semantic analysis
* Interview question generation
* Multi-role support beyond software jobs

---

## 🎓 Academic Relevance

This project demonstrates:

* Full-stack development
* REST API integration
* AI-powered text processing
* Data visualization
* Authentication
* PDF report generation
* Database design

Suitable for:

* Mini Projects
* Major Projects
* Placement Management Systems
* Research Prototypes

---

## 📝 Sample Project Title

**AI-Powered Resume Analyzer with ATS Scoring, Skills Gap Analysis, Career Recommendations, and LinkedIn Job Integration**.

---

## 👨‍💻 Author

**Mohammad Musaib**
Computer Science Engineering Student
Web Developer | Java Developer | Full Stack Enthusiast

---

## 📜 License

This project is created for educational and academic purposes.

---

## ⭐ Acknowledgements

* Spring Boot
* React.js
* FastAPI
* PyMuPDF
* Recharts
* LinkedIn Jobs
* IEEE project inspiration

---

## 🏁 Conclusion

AI Resume Analyzer is a comprehensive recruitment assistance platform that automates resume screening and provides actionable insights to both placement officers and job seekers. It combines AI, analytics, and modern web technologies into a professional academic project.
