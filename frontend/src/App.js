// Full cleaned App.js code
// Copy and replace everything in frontend/src/App.js

import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";
import AdminLogin from "./components/AdminLogin";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  CartesianGrid,
  Legend,
} from "recharts";

function App() {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [adminStats, setAdminStats] = useState(null);

  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(
    localStorage.getItem("isAdminLoggedIn") === "true"
  );

  // Sample Analytics Data
  const scoreDistribution = [
    { range: "0-20", count: 2 },
    { range: "21-40", count: 5 },
    { range: "41-60", count: 12 },
    { range: "61-80", count: 24 },
    { range: "81-100", count: 31 },
  ];

  const missingSkillsData = [
    { name: "AWS", value: 15 },
    { name: "Spring Boot", value: 12 },
    { name: "Docker", value: 10 },
    { name: "Python", value: 8 },
    { name: "Git", value: 6 },
  ];

  const roleData = [
    { role: "Full Stack", count: 20 },
    { role: "Backend", count: 15 },
    { role: "Frontend", count: 12 },
    { role: "DevOps", count: 8 },
  ];

  const monthlyTrend = [
    { month: "Jan", resumes: 10 },
    { month: "Feb", resumes: 15 },
    { month: "Mar", resumes: 22 },
    { month: "Apr", resumes: 28 },
    { month: "May", resumes: 35 },
    { month: "Jun", resumes: 42 },
  ];

  const COLORS = [
    "#2563eb",
    "#10b981",
    "#f59e0b",
    "#8b5cf6",
    "#ef4444",
  ];

  useEffect(() => {
    if (isAdminLoggedIn) {
      loadAdminStats();
    }
  }, [isAdminLoggedIn]);

  const loadAdminStats = async () => {
    try {
      const response = await axios.get("https://ai-resume-analyzer-backend-z6g8.onrender.com/api/admin/stats");
      setAdminStats(response.data);
    } catch (error) {
      console.error("Failed to load admin stats", error);
    }
  };

  const analyzeResume = async () => {
    if (!file) {
      alert("Please select a PDF resume.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      const response = await axios.post(
        "https://ai-resume-analyzer-backend-z6g8.onrender.com/api/resumes/upload-and-analyze",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      setResult(response.data);
    } catch (error) {
      console.error(error);
      alert("Resume analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  const matchJobDescription = async () => {
    if (!file) {
      alert("Please upload a resume first.");
      return;
    }

    if (!jobDescription.trim()) {
      alert("Please enter a job description.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("jobDescription", jobDescription);

    try {
      setLoading(true);
      const response = await axios.post(
        "https://ai-resume-analyzer-backend-z6g8.onrender.com/api/resumes/match-job",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      setMatchResult(response.data);
    } catch (error) {
      console.error(error);
      alert("Job matching failed.");
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async () => {
    if (!file) {
      alert("Please upload a resume first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "https://ai-resume-analyzer-backend-z6g8.onrender.com/api/resumes/generate-report",
        formData,
        {
          responseType: "blob",
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "resume-analysis-report.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error(error);
      alert("PDF generation failed.");
    }
  };

  if (!isAdminLoggedIn) {
    return (
      <AdminLogin
        onLogin={() => {
          localStorage.setItem("isAdminLoggedIn", "true");
          setIsAdminLoggedIn(true);
        }}
      />
    );
  }

  return (
    <div className="app-container">
      <h1>AI Resume Analyzer</h1>
      <p className="subtitle">
        Upload your resume and get AI-powered feedback.
      </p>

      {adminStats && (
        <div className="section">
          <h3>Admin Dashboard</h3>

          <button
            onClick={() => {
              localStorage.removeItem("isAdminLoggedIn");
              setIsAdminLoggedIn(false);
            }}
            style={{
              width: "auto",
              padding: "10px 20px",
              marginBottom: "20px",
              background: "#ef4444",
              color: "white",
              border: "none",
              borderRadius: "8px",
              fontWeight: "600",
              cursor: "pointer",
            }}
          >
            Logout
          </button>

          <ul>
            <li><strong>Total Resumes Analyzed:</strong> {adminStats.totalResumes}</li>
            <li><strong>Average ATS Score:</strong> {adminStats.averageScore}</li>
            <li><strong>Highest Score:</strong> {adminStats.highestScore}</li>
            <li><strong>Top Missing Skill:</strong> {adminStats.topMissingSkill}</li>
            <li><strong>Top Recommended Role:</strong> {adminStats.topRecommendedRole}</li>
          </ul>
        </div>
      )}

      <div className="charts-section">
        <h2>Analytics Dashboard</h2>
        <div className="charts-grid">
          <div className="chart-card">
            <h3>ATS Score Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scoreDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <h3>Top Missing Skills</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={missingSkillsData} dataKey="value" nameKey="name" outerRadius={100} label>
                  {missingSkillsData.map((entry, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <h3>Recommended Roles</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={roleData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="role" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <h3>Monthly Trend</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={monthlyTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="resumes" stroke="#8b5cf6" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <input
        type="file"
        accept=".pdf"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button className="analyze-btn" onClick={analyzeResume} disabled={loading}>
        {loading ? "Analyzing..." : "Analyze Resume"}
      </button>

      <textarea
        placeholder="Paste the job description here..."
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
      />

      <button className="match-btn" onClick={matchJobDescription} disabled={loading}>
        Match with Job Description
      </button>

      <button className="download-btn" onClick={downloadReport}>
        Download PDF Report
      </button>

      {result && (
        <div className="result-card">
          <div className="score-box">
            <h2>{result.score}/100</h2>
            <p>Resume Score • Word Count: {result.word_count}</p>
          </div>

          <div className="section">
            <h3>Strengths</h3>
            <ul>
              {result.strengths?.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="section">
            <h3>Missing Keywords</h3>
            <ul>
              {(result.missing_keywords || result.missingKeywords)?.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="section">
            <h3>Suggestions</h3>
            <ul>
              {result.suggestions?.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {matchResult && (
        <div className="match-card">
          <h2>{matchResult.match_percentage}% Match</h2>

          <h3>Matched Keywords</h3>
          <ul>
            {matchResult.matched_keywords?.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>

          <h3>Missing Keywords</h3>
          <ul>
            {matchResult.missing_keywords?.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>

          <h3>Recommendations</h3>
          <ul>
            {matchResult.recommendations?.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>

          <h3>Skills Gap Analysis</h3>
          <ul>
            <li><strong>Missing Skills Count:</strong> {matchResult.skill_gap_count}</li>
            <li><strong>Potential Improvement:</strong> +{matchResult.potential_improvement}%</li>
          </ul>

          <h3>Priority Skills to Learn</h3>
          <ul>
            {matchResult.priority_skills?.map((skill, index) => (
              <li key={index}>{skill}</li>
            ))}
          </ul>

          <h3>Recommended Career Roles</h3>
          <ul>
            {matchResult.career_recommendations?.map((role, index) => (
              <li
                key={index}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "10px",
                }}
              >
                <span>{role}</span>
                <button
                  type="button"
                  onClick={() =>
                    window.open(
                      `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(role)}`,
                      "_blank"
                    )
                  }
                  style={{
                    width: "auto",
                    padding: "8px 14px",
                    marginTop: 0,
                    fontSize: "0.9rem",
                    background: "#0A66C2",
                    color: "white",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                  }}
                >
                  Visit LinkedIn Jobs
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
