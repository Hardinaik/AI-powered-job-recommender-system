import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api/axios";
import "./Auth.css";
import Login from "./Login";
 
function SignUp() {
  const navigate = useNavigate();
 
  const [showLogin, setShowLogin] = useState(false);
  const [role, setRole] = useState("jobseeker");
  const [fullname, setFullname] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
 
  if (showLogin) {
    return <Login />;
  }
 
  const handleSignup = async () => {
    setError("");
 
    if (!fullname || !email || !password) {
      setError("All fields are required.");
      return;
    }
 
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
 
    try {
      setLoading(true);
 
      const response = await api.post("/auth/signup", {
        fullname,
        email,
        password,
        user_role: role,
      });
 
      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("role", response.data.role);
 
      if (response.data.role === "recruiter") navigate("/recruiter-dashboard");
      else navigate("/joblist");
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) setError(detail[0].msg);
      else setError(detail || "Signup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };
 
  const handleKeyDown = (e) => { if (e.key === "Enter") handleSignup(); };
 
  return (
    <div className="login-container">
      <div className="login-card">
 
        {/* Brand */}
        <div className="auth-brand">
          <span className="auth-brand-dot" />
          <span className="auth-brand-name">JobConnect</span>
        </div>
 
        <h2 className="login-title">Create an account</h2>
        <p className="login-subtitle">Join as a job seeker or recruiter</p>
 
        <div className="auth-divider" />
 
        <div className="role-toggle">
          <button
            className={role === "jobseeker" ? "active" : ""}
            onClick={() => setRole("jobseeker")}
          >
            Job Seeker
          </button>
          <button
            className={role === "recruiter" ? "active" : ""}
            onClick={() => setRole("recruiter")}
          >
            Recruiter
          </button>
        </div>
 
        <div className="form-group">
          <label>{role === "recruiter" ? "Company Name" : "Full Name"}</label>
          <input
            type="text"
            placeholder={role === "recruiter" ? "e.g. Acme Corp" : "e.g. Alex Johnson"}
            value={fullname}
            onChange={(e) => setFullname(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>
 
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
            placeholder="Min. 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>
 
        {error && <p className="error-text">⚠ {error}</p>}
 
        <button className="create-btn" onClick={handleSignup} disabled={loading}>
          {loading ? "Creating account…" : "Create Account"}
        </button>
 
        <p className="signup-text">
          Already have an account?{" "}
          <button onClick={() => setShowLogin(true)}>Sign in</button>
        </p>
 
      </div>
    </div>
  );
}
 
export default SignUp;