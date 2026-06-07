import React, { useState } from "react";
import axios from "axios";
import "./AdminLogin.css";
import { toast } from "react-hot-toast";
import { motion } from "framer-motion";
import CONFIG from "../config";

const AdminLogin = ({ onLogin, sessionExpired, onDismissExpiry }) => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const resp = await axios.post(`${CONFIG.API_BASE_URL}/auth/login`, { username, password });
            onLogin(resp.data.token);
            toast.success("Welcome back, Administrator");
        } catch (err) {
            toast.error(err.response?.data?.error || "Invalid credentials");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            {sessionExpired && (
                <motion.div
                    initial={{ y: -50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="session-banner"
                >
                    <span>Session expired. Please log in again.</span>
                    <button onClick={onDismissExpiry}>✕</button>
                </motion.div>
            )}

            <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.4 }}
                className="login-card glass-panel"
            >
                <div className="login-header">
                    <div className="admin-icon">🔑</div>
                    <h2>Admin Secure Access</h2>
                    <p>Portfolio Analytics & Insights</p>
                </div>
                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <input
                            type="text"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>
                    <div className="input-group">
                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button type="submit" className="login-btn" disabled={loading}>
                        {loading ? <span className="spinner"></span> : "Sign In to Dashboard"}
                    </button>
                </form>
                <p className="login-hint">Restricted access for system administrators only.</p>
            </motion.div>
        </div>
    );
};

export default AdminLogin;