import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api/axios";  
import "./Auth.css";
import SignUp from "./SignUp";

function Login() {
  const [showSignUp, setShowSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  // If user clicks signup
  if (showSignUp) {
    return <SignUp />;
  }

  const handleLogin = async () => {
    try {
      const response = await api.post("/auth/login", {
        email,
        password,
      });

      const { access_token, role } = response.data;

      // Store token & role in localStorage
      localStorage.setItem("token", access_token);
      localStorage.setItem("role", role);

      
      // Redirect based on role
      if (role === "jobseeker") {
        navigate("/joblist");
      } else if (role === "recruiter") {
        navigate("/recruiter-dashboard");
      }

    } catch (error) {
      console.error(error);
      alert(
        error.response?.data?.detail || "Login failed. Please try again."
      );
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2 className="login-title">Sign in</h2>

        <div className="form-group">
          <label>Email Address</label>
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <div className="forgot-password">
          <a href="#">Forgot Password?</a>
        </div>

        <button className="login-btn" onClick={handleLogin}>
          Login
        </button>

        <p className="signup-text">
          Not registered yet?{" "}
          <button onClick={() => setShowSignUp(true)}>
            Sign up
          </button>
        </p>
      </div>
    </div>
  );
}

export default Login;
