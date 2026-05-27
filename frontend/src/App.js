import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import "./App.css";
import AdminLogin from "./components/AdminLogin";
import OptimizationList from "./components/OptimizationList";
import InterviewCoach from "./components/InterviewCoach";
import CONFIG from "./config";
import {
  BarChart,
  Bar,
  XAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from "recharts";

const API_BASE_URL = CONFIG.API_BASE_URL;

// ── Auth helpers ─────────────────────────────────────────────────────────────
const getToken = () => localStorage.getItem("adminToken");

const getAuthHeaders = () => {
  const token = getToken();
  return token ? { headers: { Authorization: `Bearer ${token}` } } : {};
};

function App() {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [adminStats, setAdminStats] = useState(null);
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(false);
  const [isVerifying, setIsVerifying] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [optimizing, setOptimizing] = useState(false);
  const [interviewResult, setInterviewResult] = useState(null);
  const [loadingCoach, setLoadingCoach] = useState(false);

  const [scoreDistribution, setScoreDistribution] = useState([
    { range: "0-20", count: 0 },
    { range: "21-40", count: 0 },
    { range: "41-60", count: 0 },
    { range: "61-80", count: 0 },
    { range: "81-100", count: 0 },
  ]);

  const [missingSkillsData, setMissingSkillsData] = useState([]);
  const [monthlyTrend, setMonthlyTrend] = useState([]);
  const [showAdminLogin, setShowAdminLogin] = useState(false);

  const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"];

  const handleLogout = useCallback((expired = false) => {
    localStorage.removeItem("adminToken");
    localStorage.removeItem("isAdminLoggedIn");
    setIsAdminLoggedIn(false);
    setAdminStats(null);
    if (expired) setSessionExpired(true);
  }, []);

  const loadAdminStats = useCallback(async (tokenToUse) => {
    try {
      const activeToken = tokenToUse || getToken();
      if (!activeToken) return;

      const headers = { headers: { Authorization: `Bearer ${activeToken}` } };
      const response = await axios.get(`${API_BASE_URL}/admin/stats`, headers);
      const data = response.data;
      setAdminStats(data);

      if (data.scoreDistribution) {
        setScoreDistribution([
          { range: "0-20", count: data.scoreDistribution[0] },
          { range: "21-40", count: data.scoreDistribution[1] },
          { range: "41-60", count: data.scoreDistribution[2] },
          { range: "61-80", count: data.scoreDistribution[3] },
          { range: "81-100", count: data.scoreDistribution[4] },
        ]);
      }

      if (data.monthlyTrend) {
        const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const trend = Object.entries(data.monthlyTrend)
          .map(([month, count]) => ({ month, resumes: count }))
          .sort((a, b) => months.indexOf(a.month) - months.indexOf(b.month));
        setMonthlyTrend(trend);
      }

      if (data.topMissingSkills) {
        setMissingSkillsData(data.topMissingSkills);
      }
    } catch (error) {
      if (error.response?.status === 401 || error.response?.status === 403) {
        handleLogout(true); // true = session expired, show banner
      } else {
        console.error("Failed to load admin stats", error);
      }
    }
  }, [handleLogout]);

  // Validate token on startup
  useEffect(() => {
    const validateToken = async () => {
      const token = getToken();
      if (!token) {
        setIsVerifying(false);
        return;
      }
      try {
        // Use dedicated validation endpoint
        await axios.post(`${API_BASE_URL}/auth/validate`, {}, getAuthHeaders());
        setIsAdminLoggedIn(true);
      } catch (e) {
        handleLogout();
      } finally {
        setIsVerifying(false);
      }
    };
    validateToken();
  }, [handleLogout]);

  useEffect(() => {
    if (isAdminLoggedIn) {
      loadAdminStats();
    }
  }, [isAdminLoggedIn, loadAdminStats]);

  const handleLogin = (token) => {
    localStorage.setItem("adminToken", token);
    localStorage.setItem("isAdminLoggedIn", "true");
    setIsAdminLoggedIn(true);
    setShowAdminLogin(false);
  };

  // ── Persistence: Load from localStorage ─────────────────────────────────────
  useEffect(() => {
    const savedResult = localStorage.getItem("last_analysis_result");
    const savedMatch = localStorage.getItem("last_match_result");
    const savedOpt = localStorage.getItem("last_optimization_result");
    const savedInterview = localStorage.getItem("last_interview_result");

    if (savedResult) setResult(JSON.parse(savedResult));
    if (savedMatch) setMatchResult(JSON.parse(savedMatch));
    if (savedOpt) setOptimizationResult(JSON.parse(savedOpt));
    if (savedInterview) setInterviewResult(JSON.parse(savedInterview));
  }, []);

  // ── Persistence: Save to localStorage ───────────────────────────────────────
  useEffect(() => {
    if (result) localStorage.setItem("last_analysis_result", JSON.stringify(result));
    if (matchResult) localStorage.setItem("last_match_result", JSON.stringify(matchResult));
    if (optimizationResult) localStorage.setItem("last_optimization_result", JSON.stringify(optimizationResult));
    if (interviewResult) localStorage.setItem("last_interview_result", JSON.stringify(interviewResult));
  }, [result, matchResult, optimizationResult, interviewResult]);

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
        `${API_BASE_URL}/resumes/upload-and-analyze`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setResult(response.data);
    } catch (error) {
      alert(error.response?.data?.error || "Resume analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  const matchJobDescription = async () => {
    if (!file || !jobDescription.trim()) {
      alert("Please upload a resume and enter a job description.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("jobDescription", jobDescription);

    try {
      setLoading(true);
      const response = await axios.post(
        `${API_BASE_URL}/resumes/match-job`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setMatchResult(response.data);
    } catch (error) {
      alert(error.response?.data?.error || "Job matching failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = async () => {
    if (!file) {
      alert("Please upload a resume first.");
      return;
    }
    const formData = new FormData();
    formData.append("file", file);

    try {
      setOptimizing(true);
      const response = await axios.post(
        `${API_BASE_URL}/resumes/optimize`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setOptimizationResult(response.data);
    } catch (error) {
      alert("AI optimization failed.");
    } finally {
      setOptimizing(false);
    }
  };

  const startInterviewPrep = async () => {
    if (!file) {
      alert("Please upload a resume first.");
      return;
    }
    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoadingCoach(true);
      const response = await axios.post(
        `${API_BASE_URL}/resumes/interview-prep`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setInterviewResult(response.data);
    } catch (error) {
      alert("Interview preparation failed.");
    } finally {
      setLoadingCoach(false);
    }
  };

  const downloadReport = async () => {
    if (!file) return alert("Please upload a resume first.");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${API_BASE_URL}/resumes/generate-report`, formData, {
        responseType: "blob",
        headers: { "Content-Type": "multipart/form-data" },
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "resume-analysis-report.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      alert("PDF generation failed.");
    }
  };

  if (isVerifying) return <div className="loading-screen">Authenticating...</div>;

  return (
    <div className="app-container">
      {showAdminLogin && !isAdminLoggedIn && (
        <AdminLogin
          onLogin={handleLogin}
          sessionExpired={sessionExpired}
          onDismissExpiry={() => setSessionExpired(false)}
          onBack={() => setShowAdminLogin(false)}
        />
      )}

      <header>
        <div className="header-top">
          <h1>AI Resume Analyzer</h1>
          {!isAdminLoggedIn && (
            <button className="admin-access-btn" onClick={() => setShowAdminLogin(true)}>
              Admin Portal
            </button>
          )}
        </div>
        <p className="subtitle">Advanced analytics and career insights platform.</p>
      </header>

      {adminStats && (
        <section className="section dashboard">
          <div className="dashboard-header">
            <h3>Admin Overview</h3>
            <button onClick={handleLogout} className="logout-btn">Sign Out</button>
          </div>

          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">{adminStats.totalResumes}</span>
              <span className="stat-label">Total Resumes</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{adminStats.analyzedResumes}</span>
              <span className="stat-label">Analyzed</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{adminStats.averageScore}</span>
              <span className="stat-label">Avg ATS Score</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{adminStats.highestScore}</span>
              <span className="stat-label">Peak Score</span>
            </div>
          </div>

          <div className="summary-insights">
            <div className="stat-item">
              <span className="stat-label">Top Missing Skill</span>
              <span className="stat-value skill-highlight">{adminStats.topMissingSkill || "N/A"}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Target Role</span>
              <span className="stat-value role-highlight">{adminStats.topRecommendedRole || "N/A"}</span>
            </div>
          </div>
        </section>
      )}

      <section className="charts-section">
        <h2>Analytics Insights</h2>
        <div className="charts-grid">
          <div className="chart-card">
            <h3>ATS Score Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={scoreDistribution}>
                <XAxis dataKey="range" stroke="#94a3b8" fontSize={12} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                  itemStyle={{ color: '#818cf8' }}
                />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <h3>Skill Gap Analysis</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={missingSkillsData}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={80}
                  innerRadius={60}
                  paddingAngle={5}
                >
                  {missingSkillsData.map((entry, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }} />
                <Legend iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <h3>Monthly Activity</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={monthlyTrend}>
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} />
                <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }} />
                <Line type="monotone" dataKey="resumes" stroke="#a855f7" strokeWidth={3} dot={{ r: 4, fill: '#a855f7' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="section core-tools">
        <div className="tool-box">
          <label className="tool-label">Upload Resume (PDF)</label>
          <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} />

          <button className="analyze-btn" onClick={analyzeResume} disabled={loading}>
            {loading ? "Processing AI Analysis..." : "Analyze Portfolio"}
          </button>

          <textarea
            placeholder="Paste Job Description for matching..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
          />

          <div className="tool-actions">
            <button className="match-btn" onClick={matchJobDescription} disabled={loading}>Compare with JD</button>
            <button className="optimize-btn" onClick={handleOptimize} disabled={loading || optimizing}>
              {optimizing ? "Generating AI Rewrites..." : "Smart Optimize"}
            </button>
            <button className="coach-btn" onClick={startInterviewPrep} disabled={loading || loadingCoach}>
              {loadingCoach ? "Coaching..." : "AI Interview Prep"}
            </button>
            <button className="download-btn" onClick={downloadReport}>Export PDF Insight Report</button>
          </div>
        </div>
      </section>

      {result && (
        <div className="result-card">
          <div className="score-box">
            <div className="score-circle">{result.score}</div>
            <p className="stat-label">ATS COMPATIBILITY SCORE</p>
            <p className="word-count-label">Word Count: {result.word_count}</p>
          </div>

          <div className="analysis-grid">
            <div className="analysis-col">
              <h3>Strengths</h3>
              <ul className="result-list">
                {result.strengths?.map((item, index) => <li key={index}>{item}</li>)}
              </ul>
            </div>

            <div className="analysis-col growth-areas">
              <h3>Growth Areas</h3>
              <ul className="result-list">
                {(result.missing_keywords || result.missingKeywords)?.map((item, index) => <li key={index}>{item}</li>)}
              </ul>
            </div>
          </div>

          <div className="suggestions-box">
            <h3>Critical Suggestions</h3>
            <ul className="result-list">
              {result.suggestions?.map((item, index) => <li key={index}>{item}</li>)}
            </ul>
          </div>

          <OptimizationList
            optimizations={optimizationResult?.optimizations}
            overallTip={optimizationResult?.overall_tip}
          />

          <InterviewCoach
            questions={interviewResult?.questions}
            overallAdvice={interviewResult?.overall_advice}
          />
        </div>
      )}

      {matchResult && (
        <div className="match-card">
          <div className="match-header">
            <div className="score-circle highlight">{matchResult.match_percentage}%</div>
            <p className="stat-label">JOB MATCH ACCURACY</p>
          </div>

          <div className="analysis-grid match-details">
            <div>
              <h3>Matched Skills</h3>
              <ul className="match-list">
                {matchResult.matched_keywords?.map((item, index) => <li key={index}>{item}</li>)}
              </ul>
            </div>
            <div>
              <h3>Missing Skills</h3>
              <ul className="match-list missing">
                {matchResult.missing_keywords?.map((item, index) => <li key={index}>{item}</li>)}
              </ul>
            </div>
          </div>

          <div className="career-recommendations">
            <h3>Recommended Career Paths</h3>
            <div className="role-links">
              {matchResult.career_recommendations?.map((role, index) => (
                <button
                  key={index}
                  onClick={() => window.open(`https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(role)}`, "_blank")}
                  className="role-link-btn"
                >
                  {role} • LinkedIn Jobs
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
