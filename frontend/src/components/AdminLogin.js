import React, { useState } from "react";
import axios from "axios";
import CONFIG from "../config";
import "./AdminLogin.css";

const API_BASE_URL = CONFIG.API_BASE_URL;

function AdminLogin({ onLogin, sessionExpired, onDismissExpiry }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [isWakingUp, setIsWakingUp] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        setIsWakingUp(false);

        const wakeTimer = setTimeout(() => setIsWakingUp(true), 5000);

        try {
            const response = await axios.post(`${API_BASE_URL}/auth/login`, {
                username,
                password,
            }, { timeout: 60000 });

            const { token } = response.data;
            onLogin(token);
        } catch (err) {
            const message = err.response?.data?.error || "Invalid username or password";
            setError(message);
        } finally {
            setLoading(false);
            setIsWakingUp(false);
            clearTimeout(wakeTimer);
        }
    };

    return (
        <div className="login-page">
            <div className="login-card">
                <div className="login-badge">🔐 Secure Admin Portal</div>

                <h1 className="login-title">AI Resume Analyzer</h1>
                <p className="login-subtitle">
                    Sign in to access analytics, ATS reports, and administrative tools.
                </p>

                {sessionExpired && (
                    <div className="session-expired-banner">
                        <span>⚠️ Your session has expired. Please sign in again.</span>
                        <button className="dismiss-btn" onClick={onDismissExpiry}>✕</button>
                    </div>
                )}

                {error && <div className="login-error">{error}</div>}

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="input-group">
                        <label>Username</label>
                        <input
                            type="text"
                            placeholder="Enter admin username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className="input-group">
                        <label>Password</label>
                        <input
                            type="password"
                            placeholder="Enter password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            disabled={loading}
                        />
                    </div>

                    <button type="submit" className="login-button" disabled={loading}>
                        {loading ? (isWakingUp ? "Waking up server..." : "Signing in...") : "Login to Dashboard"}
                    </button>
                    {isWakingUp && (
                        <p className="login-hint">
                            The server was sleeping. This take ~45s to wake up on the first try!
                        </p>
                    )}
                </form>
            </div>
        </div>
    );
}

export default AdminLogin;