import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { AiOutlineEye, AiOutlineEyeInvisible } from "react-icons/ai";
import api from "../../api/axios";
import "./ResetPassword.css"

export default function ResetPassword() {
  const [params]   = useSearchParams();
  const navigate   = useNavigate();
  const token      = params.get("token");

  const [password,  setPassword]  = useState("");
  const [confirm,   setConfirm]   = useState("");
  const [showPw,    setShowPw]    = useState(false);
  const [showCf,    setShowCf]    = useState(false);
  const [error,     setError]     = useState("");
  const [loading,   setLoading]   = useState(false);
  const [success,   setSuccess]   = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirm)   return setError("Passwords do not match");
    if (password.length < 8)    return setError("Password must be at least 8 characters");

    setLoading(true);
    setError("");
    try {
      await api.post("/auth/passwords/reset-password", { token, new_password: password });
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || "This link is invalid or has expired.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="reset-container">
        <div className="reset-card">
          <p style={{ color: "var(--text-muted)", fontSize: 14 }}>
            Invalid reset link. Please request a new one.
          </p>
          <div className="back-to-login">
            <button onClick={() => navigate("/login")}>Back to login</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="reset-container">
      <div className="reset-card">

        {/* ── Success state ── */}
        {success ? (
          <div className="reset-success">
            <h2 className="reset-title">Password updated</h2>
            <p>Your password has been reset successfully. You can now sign in with your new password.</p>
            <div>
              <button className="login-btn" onClick={() => navigate("/login")}>Go to login</button>
            </div>
          </div>
        ) : (

          /* ── Form state ── */
          <>
            <h2 className="reset-title">Set new password</h2>
            <p className="reset-subtitle">Must be at least 8 characters.</p>

            <form onSubmit={handleSubmit} style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 14 }}>

              {/* New password */}
              <div className="password-wrapper">
                <input
                  type={showPw ? "text" : "password"}
                  required
                  minLength={8}
                  placeholder="New password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  className="toggle-eye"
                  onClick={() => setShowPw(v => !v)}
                  aria-label={showPw ? "Hide password" : "Show password"}
                >
                  {showPw ? <AiOutlineEyeInvisible /> : <AiOutlineEye />}
                </button>
              </div>

              {/* Confirm password */}
              <div className="password-wrapper">
                <input
                  type={showCf ? "text" : "password"}
                  required
                  placeholder="Confirm password"
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                />
                <button
                  type="button"
                  className="toggle-eye"
                  onClick={() => setShowCf(v => !v)}
                  aria-label={showCf ? "Hide confirm password" : "Show confirm password"}
                >
                  {showCf ? <AiOutlineEyeInvisible /> : <AiOutlineEye />}
                </button>
              </div>

              {/* Error */}
              {error && (
                <p style={{ color: "#ef4444", fontSize: 13, margin: 0 }}>
                  {error}
                </p>
              )}

              {/* Submit */}
              <button className="submit-btn" type="submit" disabled={loading}>
                {loading ? "Updating…" : "Reset password"}
              </button>
            </form>

            <div className="back-to-login">
              <button onClick={() => navigate("/login")}>Back to login</button>
            </div>
          </>
        )}

      </div>
    </div>
  );
}