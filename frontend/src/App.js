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
  const [isWakingUp, setIsWakingUp] = useState(false);
  const [analysisLogs, setAnalysisLogs] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [scoreDistribution, setScoreDistribution] = useState([
    { range: "0-20", count: 0 },
    { range: "21-40", count: 0 },
    { range: "41-60", count: 0 },
    { range: "61-80", count: 0 },
    { range: "81-100", count: 0 },
  ]);

  const [missingSkillsData, setMissingSkillsData] = useState([]);
  const [monthlyTrend, setMonthlyTrend] = useState([]);

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

  // ── Pre-warm: Trigger server wake-up ──────────────────────────────────────
  useEffect(() => {
    const wakeTimer = setTimeout(() => setIsWakingUp(true), 5000);

    // Ping backend (silently pre-warm)
    const p1 = axios.post(`${API_BASE_URL}/auth/validate`, {}, { timeout: 60000 }).catch(() => { });
    // Ping AI service (silently pre-warm)
    const p2 = axios.get(CONFIG.AI_SERVICE_URL, { timeout: 60000 }).catch(() => { });

    Promise.allSettled([p1, p2]).finally(() => {
      clearTimeout(wakeTimer);
      setIsWakingUp(false);
    });
  }, []);

  useEffect(() => {
    if (isAdminLoggedIn) {
      loadAdminStats();
    }
  }, [isAdminLoggedIn, loadAdminStats]);

  const handleLogin = (token) => {
    localStorage.setItem("adminToken", token);
    localStorage.setItem("isAdminLoggedIn", "true");
    setIsAdminLoggedIn(true);
  };


  const addLog = (msg, type = "info") => {
    const time = new Date().toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
    setAnalysisLogs((prev) => [...prev, { msg, type, time, id: Date.now() + Math.random() }]);
  };

  const analyzeResume = async () => {
    if (!file) {
      alert("Please select a PDF resume.");
      return;
    }

    setAnalysisLogs([]);
    setIsAnalyzing(true);
    addLog("Initializing CareerIQ AI Engine...", "info");

    const formData = new FormData();
    formData.append("file", file);

    try {
      setTimeout(() => addLog("Handshaking with Python AI Service...", "info"), 600);
      setTimeout(() => addLog("Running spaCy POS tagging for impact verbs...", "info"), 1400);
      setTimeout(() => addLog("Detecting quantified achievements & metrics...", "info"), 2200);
      setTimeout(() => addLog("Matching skill taxonomy against 150+ keywords...", "info"), 3000);

      const response = await axios.post(
        `${API_BASE_URL}/resumes/upload-and-analyze`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      addLog("Analysis complete! Ranking results...", "success");
      setTimeout(() => {
        setResult(response.data);
        setIsAnalyzing(false);
      }, 800);
    } catch (error) {
      addLog("Critical error during analysis.", "error");
      alert(error.response?.data?.error || "Resume analysis failed.");
      setIsAnalyzing(false);
    }
  };

  const matchJobDescription = async () => {
    if (!file || !jobDescription.trim()) {
      alert("Please upload a resume and enter a job description.");
      return;
    }

    setAnalysisLogs([]);
    setIsAnalyzing(true);
    addLog("Initializing Job Match Engine...", "info");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("jobDescription", jobDescription);

    try {
      setTimeout(() => addLog("Analyzing Job Description semantic requirements...", "info"), 500);
      setTimeout(() => addLog("Comparing resume features against JD criteria...", "info"), 1500);

      const response = await axios.post(
        `${API_BASE_URL}/resumes/match-job`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      addLog("Job Match complete!", "success");
      setTimeout(() => {
        setMatchResult(response.data);
        setIsAnalyzing(false);
      }, 800);
    } catch (error) {
      addLog("Job matching failed.", "error");
      alert(error.response?.data?.error || "Job matching failed.");
      setIsAnalyzing(false);
    }
  };

  const handleOptimize = async () => {
    if (!file) {
      alert("Please upload a resume first.");
      return;
    }

    setAnalysisLogs([]);
    setIsAnalyzing(true);
    addLog("Initializing Smart Optimizer...", "info");

    const formData = new FormData();
    formData.append("file", file);

    try {
      setTimeout(() => addLog("Scanning for structural improvements...", "info"), 600);
      setTimeout(() => addLog("Generating metric-based bullet point rewrites...", "info"), 1400);

      const response = await axios.post(
        `${API_BASE_URL}/resumes/optimize`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      addLog("Optimization scripts generated!", "success");
      setTimeout(() => {
        setOptimizationResult(response.data);
        setIsAnalyzing(false);
      }, 800);
    } catch (error) {
      addLog("Optimizer failed.", "error");
      alert("AI optimization failed.");
      setIsAnalyzing(false);
    }
  };

  const startInterviewPrep = async () => {
    if (!file) {
      alert("Please upload a resume first.");
      return;
    }

    setAnalysisLogs([]);
    setIsAnalyzing(true);
    addLog("Summoning AI Interview Coach...", "info");

    const formData = new FormData();
    formData.append("file", file);

    try {
      setTimeout(() => addLog("Extracting candidate technical persona...", "info"), 700);
      setTimeout(() => addLog("Generating tailored technical questions...", "info"), 1600);
      setTimeout(() => addLog("Consulting behavioral interview standards...", "info"), 2500);

      const response = await axios.post(
        `${API_BASE_URL}/resumes/interview-prep`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      addLog("Coach is ready!", "success");
      setTimeout(() => {
        setInterviewResult(response.data);
        setIsAnalyzing(false);
      }, 1000);
    } catch (error) {
      addLog("Coach failed.", "error");
      alert("Interview preparation failed.");
      setIsAnalyzing(false);
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

  if (isVerifying) {
    return (
      <div className="loading-screen">
        <div className="loader"></div>
        <h2>{isWakingUp ? "Waking up server..." : "Authenticating..."}</h2>
        {isWakingUp && <p className="loading-hint">This takes about 45s on the first visit because of Render's free tier sleep mode. Hang tight!</p>}
      </div>
    );
  }

  if (!isAdminLoggedIn) {
    return <AdminLogin onLogin={handleLogin} sessionExpired={sessionExpired} onDismissExpiry={() => setSessionExpired(false)} />;
  }

  return (
    <div className="app-container">
      <header>
        <h1>AI Resume Analyzer</h1>
        <p className="subtitle">Advanced analytics and career insights platform.</p>
      </header>

      {isAnalyzing && (
        <div className="analysis-overlay">
          <div className="analysis-terminal">
            <div className="terminal-header">
              <span className="dot red"></span>
              <span className="dot yellow"></span>
              <span className="dot green"></span>
              <span className="terminal-title">AI Scanner v2.0 - Real-time Analysis</span>
            </div>
            <div className="terminal-body">
              {analysisLogs.map((log, i) => (
                <div key={i} className={`log-line ${log.type}`}>
                  <span className="log-time">[{log.time}]</span>
                  <span className="log-msg">{log.msg}</span>
                </div>
              ))}
              <div className="cursor">_</div>
            </div>
          </div>
        </div>
      )}

      {adminStats && adminStats.totalResumes > 0 ? (
        <>
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
        </>
      ) : (
        <section className="section welcome-box">
          <div className="dashboard-header">
            <h3>Welcome to your AI Dashboard</h3>
            <button onClick={handleLogout} className="logout-btn">Sign Out</button>
          </div>
          <p>Get started by uploading your first resume below. Your career insights and analytics will appear here as soon as you analyze a portfolio.</p>
        </section>
      )}

      <section className="section core-tools">
        <div className="tool-box">
          <label className="tool-label">Upload Resume (PDF)</label>
          <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} />

          <button className="analyze-btn" onClick={analyzeResume} disabled={isAnalyzing}>
            {isAnalyzing ? "Processing AI Analysis..." : "Analyze Portfolio"}
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
