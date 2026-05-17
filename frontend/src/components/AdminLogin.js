import React, { useState } from "react";
import "./AdminLogin.css";
function AdminLogin({ onLogin }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const handleSubmit = (e) => {
        e.preventDefault();

        // Demo credentials
        if (username === "admin" && password === "admin123") {
            localStorage.setItem("isAdminLoggedIn", "true");
            onLogin(); // Notify parent component
        } else {
            setError("Invalid username or password");
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
                        />
                    </div>

                    <button type="submit" className="login-button">
                        Login to Dashboard
                    </button>
                </form>

                <div className="login-footer">
                    <p><strong>Demo Credentials</strong></p>
                    <p>Username: <code>admin</code></p>
                    <p>Password: <code>admin123</code></p>
                </div>
            </div>
        </div>
    );

}
export default AdminLogin;