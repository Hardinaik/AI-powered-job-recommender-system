import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import axios from "axios";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token");

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirm) return setError("Passwords do not match");
    if (password.length < 8) return setError("Password must be at least 8 characters");

    setLoading(true);
    setError("");
    try {
      await axios.post("/auth/passwords/reset-password", { token, new_password: password });
      navigate("/login?reset=success");
    } catch (err) {
      setError(err.response?.data?.detail || "This link is invalid or has expired.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) return <p>Invalid reset link. Please request a new one.</p>;

  return (
    <form onSubmit={handleSubmit}>
      <h2>Set new password</h2>
      <input
        type="password" required minLength={8}
        placeholder="New password" value={password}
        onChange={e => setPassword(e.target.value)}
      />
      <input
        type="password" required
        placeholder="Confirm password" value={confirm}
        onChange={e => setConfirm(e.target.value)}
      />
      {error && <p style={{ color: "red" }}>{error}</p>}
      <button type="submit" disabled={loading}>
        {loading ? "Updating…" : "Reset password"}
      </button>
    </form>
  );
}