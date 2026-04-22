import { useState } from "react";
import api from "../../api/axios";
import "./ForgotPassword.css";

export default function ForgotPassword({ onClose }) {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/passwords/forgot-password", { email });
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay forgot-password-modal" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>

        <button className="modal-close" onClick={onClose}>✕</button>

        

        <h2 className="login-title">Forgot password</h2>
        <p className="login-subtitle">We'll send a reset link to your email</p>

        <div className="auth-divider" />

        {submitted ? (
          <div className="forgot-success">
            <p className="forgot-success-title">Check your inbox</p>
            <p className="forgot-success-text">
               Reset link has been sent. Check your inbox.
            </p>
            <button className="login-btn" onClick={onClose}>Back to login</button>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(""); }}
                placeholder="your@email.com"
              />
            </div>

            {error && (
              <div className="error-text">
                 {error}
              </div>
            )}

            <button className="login-btn" type="submit" disabled={loading}>
              {loading ? "Sending…" : "Send reset link"}
            </button>

            <p className="signup-text">
              Remembered it?{" "}
              <button type="button" onClick={onClose}>Back to login</button>
            </p>
          </form>
        )}

      </div>
    </div>
  );
}