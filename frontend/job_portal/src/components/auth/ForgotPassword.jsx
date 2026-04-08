import { useState } from "react";
import axios from "axios";

export default function ForgotPassword({ onClose }) {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post("/auth/passwords/forgot-password", { email });
    } catch (_) {
      // Silently ignore — prevents email enumeration
    } finally {
      setSubmitted(true);
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>

        <button className="modal-close" onClick={onClose}>✕</button>

        <h2 className="login-title">Forgot password</h2>
        <p className="login-subtitle">We'll send a reset link to your email</p>

        {submitted ? (
          <>
            <p style={{ margin: "1.2rem 0" }}>
              If this email is registered, a reset link has been sent. Check your inbox.
            </p>
            <button className="login-btn" onClick={onClose}>Close</button>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
              />
            </div>
            <button className="login-btn" type="submit" disabled={loading}>
              {loading ? "Sending…" : "Send reset link"}
            </button>
          </form>
        )}

      </div>
    </div>
  );
}