import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api/axios";
import "./Auth.css";

function SignUp() {
  const navigate = useNavigate();

  const [role, setRole] = useState("jobseeker");
  const [fullname, setFullname] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

    const handleSignup = async () => {
    setError("");

    if (!fullname || !email || !password) {
      setError("All fields are required");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long");
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

      // ✅ Save token & role
      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("role", response.data.role);

      // ✅ Redirect based on role
      if (response.data.role === "recruiter") {
        navigate("/recruiter-dashboard");
      } else {
        navigate("/joblist");
      }

    } catch (err) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Signup failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2 className="login-title">Sign Up</h2>

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
            placeholder="Enter name"
            value={fullname}
            onChange={(e) => setFullname(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Email Address</label>
          <input
            type="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            placeholder="Min. 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {error && <p className="error-text">{error}</p>}

        <button
          className="create-btn"
          onClick={handleSignup}
          disabled={loading}
        >
          {loading ? "Creating..." : "Create Account"}
        </button>

        
      </div>
    </div>
  );
}

export default SignUp;
