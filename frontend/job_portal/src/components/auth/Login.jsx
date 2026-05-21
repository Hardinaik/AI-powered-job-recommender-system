import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api/axios";
import { setAccessToken, setUserRole } from "../../api/tokenStore";
import "./Auth.css";
import SignUp from "./SignUp";
import ForgotPassword from "./ForgotPassword";

function Login() {
    const [showSignUp, setShowSignUp] = useState(false);
    const [showForgotPassword, setShowForgotPassword] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    if (showSignUp) return <SignUp />;

    const handleLogin = async () => {
        setError("");

        if (!email.trim() || !password.trim()) {
            setError("Please enter both email and password.");
            return;
        }

        try {
            setLoading(true);
            const response = await api.post("/auth/login", { email, password });
            const { access_token, role } = response.data;

           
            setAccessToken(access_token);
            setUserRole(role);

            if (role === "jobseeker") navigate("/joblist");
            else if (role === "recruiter") navigate("/recruiter-dashboard");
        } catch (err) {
            setError(err.response?.data?.detail || "Login failed. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => { if (e.key === "Enter") handleLogin(); };

    return (
        <div className="login-container">
            <div className="login-card">

                <div className="auth-brand">
                    <span className="auth-brand-dot" />
                    <span className="auth-brand-name">JobConnect</span>
                </div>

                <h2 className="login-title">Welcome back</h2>
                <p className="login-subtitle">Sign in to your account to continue</p>

                <div className="auth-divider" />

                <div className="form-group">
                    <label>Email Address</label>
                    <input
                        type="email"
                        placeholder="name@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                </div>

                <div className="form-group">
                    <label>Password</label>
                    <input
                        type="password"
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                </div>

                <div className="forgot-password">
                    <button
                        className="forgot-password-link"
                        onClick={() => setShowForgotPassword(true)}
                    >
                        Forgot password?
                    </button>
                </div>

                {error && <p className="error-text">{error}</p>}

                <button className="login-btn" onClick={handleLogin} disabled={loading}>
                    {loading ? "Signing in…" : "Sign In"}
                </button>

                <p className="signup-text">
                    Not registered yet?{" "}
                    <button onClick={() => setShowSignUp(true)}>Sign up</button>
                </p>

            </div>

            {showForgotPassword && (
                <ForgotPassword onClose={() => setShowForgotPassword(false)} />
            )}
        </div>
    );
}

export default Login;