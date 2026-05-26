# 🚀 AI Resume Analyzer Project Guide

This guide provides a simple explanation of all the key files and folders in your project.

---

## 🌍 Infrastructure & Deployment

### 📄 [render.yaml](file:///c:/Users/Samsung/OneDrive/Desktop/Resume-analyzer/render.yaml)
**The "Blueprint" of your app.** This file tells Render.com exactly how to set up your three services (Frontend, Backend, and AI Service), how they connect to each other, and what environment variables they need.

---

## 🖥️ Backend (Java Spring Boot)
Located in `backend/`

### 📄 [ResumeController.java](file:///c:/Users/Samsung/OneDrive/Desktop/Resume-analyzer/backend/src/main/java/com/musaib/resumeanalyzer/controller/ResumeController.java)
The **Receptionist**. It handles all the web requests coming from your frontend (uploading files, moving to analysis, etc.).

### 📄 [ResumeService.java](file:///c:/Users/Samsung/OneDrive/Desktop/Resume-analyzer/backend/src/main/java/com/musaib/resumeanalyzer/service/ResumeService.java)
The **Brain**. This is where the magic happens. It saves your PDFs, calls the AI service for analysis, and generates the PDF reports.

### 📄 [SecurityConfig.java](file:///c:/Users/Samsung/OneDrive/Desktop/Resume-analyzer/backend/src/main/java/com/musaib/resumeanalyzer/config/SecurityConfig.java)
The **Bouncer**. It ensures that only authorized users (Admins) can see the dashboard, while letting anyone upload a resume for analysis.

### 📄 [application.properties](file:///c:/Users/Samsung/OneDrive/Desktop/Resume-analyzer/backend/src/main/resources/application.properties)
The **Settings Page**. Contains database connections, AI service links, and security keys.

---

## 🤖 AI Service (Python FastAPI)
Located in `ai-service/`

### 📄 [main.py](file:///c:/Users/Samsung/OneDrive/Desktop/Resume-analyzer/ai-service/main.py)
The **AI Expert**. It uses Python libraries (`PyMuPDF`) to read your PDF, scan for keywords, calculate the ATS score, and suggest improvements.

### 📄 [Dockerfile](file:///c:/Users/Samsung/OneDrive/Desktop/Resume-analyzer/ai-service/Dockerfile)
The **Instruction Manual**. It tells the cloud how to install Python and all the dependencies needed to run the AI engine.

---

## 🎨 Frontend (React)
Located in `frontend/`

### 📄 [App.js](file:///c:/Users/Samsung/OneDrive/Desktop/Resume-analyzer/frontend/src/App.js)
The **Main Page**. This is the entire single-page application you see in your browser. It manages the screens, buttons, and data display.

### 📄 [config.js](file:///c:/Users/Samsung/OneDrive/Desktop/Resume-analyzer/frontend/src/config.js)
The **Navigator**. It intelligently finds your backend URL, whether you are running locally or on Render.com.

---

## 📂 Other Important Files

### 📄 [docker-compose.yml](file:///c:/Users/Samsung/OneDrive/Desktop/Resume-analyzer/docker-compose.yml)
Used for **Local Development**. It lets you run the whole project (Backend + AI) on your computer with a single command.

### 📄 [PROJECT_GUIDE.md](file:///c:/Users/Samsung/OneDrive/Desktop/Resume-analyzer/PROJECT_GUIDE.md)
This file! Your go-to reference for project structure.
