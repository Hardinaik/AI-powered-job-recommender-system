import { useState, useEffect } from "react";
import api from "../api/axios";
import "./ApplyModal.css";

function ApplyModal({ job, onClose, onApplied }) {
  const [step, setStep] = useState("loading"); // loading | form | submitting | success | error
  const [errorMsg, setErrorMsg] = useState("");

  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    experience: 0,
    resume_url: "",
    github: "",
    linkedin: "",
    why_interested: "",
  });

  // Prefill form from DB on mount
  useEffect(() => {
    const fetchPrefill = async () => {
      try {
        const { data } = await api.get(`/notifications/jobs/${job.job_id}/apply/prefill`);
        setForm((prev) => ({
          ...prev,
          name:       data.name       ?? "",
          email:      data.email      ?? "",
          phone:      data.phone      ?? "",
          experience: data.experience ?? 0,
          resume_url: data.resume_url ?? "",
        }));
        setStep("form");
      } catch {
        setStep("form"); // still show form even if prefill fails
      }
    };
    fetchPrefill();
  }, [job.job_id]);

  // Close on Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: name === "experience" ? Number(value) : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.why_interested.trim()) {
      setErrorMsg("Please tell us why you're interested in this role.");
      return;
    }
    setErrorMsg("");
    setStep("submitting");

    try {
      // Step 1: Save to DB
      await api.post(`/applications/jobs/${job.job_id}/apply`);
    } catch (err) {
      if (err.response?.status !== 409) {
        setErrorMsg(err.response?.data?.detail || "Failed to submit application.");
        setStep("form");
        return;
      }
      // 409 = already applied — still send emails
    }

    try {
      // Step 2: Send emails
      await api.post(`/notifications/jobs/${job.job_id}/apply/notify`, {
        name:           form.name,
        email:          form.email,
        phone:          form.phone      || null,
        experience:     form.experience,
        resume_url:     form.resume_url || null,
        linkedin:       form.linkedin   || null,
        why_interested: form.why_interested,
      });
    } catch {
      // Emails failed but application was saved — still treat as success
    }

    setStep("success");
    if (onApplied) onApplied(job.job_id);
  };

  const company = job.company_name || "the company";

  return (
    <div className="modal-backdrop" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal-box" role="dialog" aria-modal="true" aria-label="Apply for job">

        {/* ── Header ── */}
        <div className="modal-header">
          <div className="modal-header-text">
            <h2 className="modal-title">{job.job_title}</h2>
            <p className="modal-subtitle">@ {company}</p>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="modal-divider" />

        {/* ── Loading ── */}
        {step === "loading" && (
          <div className="modal-center">
            <div className="modal-spinner" />
            <p className="modal-hint">Loading your profile…</p>
          </div>
        )}

        {/* ── Success ── */}
        {step === "success" && (
          <div className="modal-center">
            <div className="modal-success-icon">✓</div>
            <h3 className="modal-success-title">Application Submitted!</h3>
            <p className="modal-hint">
              The recruiter has been notified. You'll receive a confirmation email shortly.
            </p>
            <button className="modal-btn-primary" onClick={onClose}>Done</button>
          </div>
        )}

        {/* ── Form ── */}
        {(step === "form" || step === "submitting") && (
          <form className="modal-form" onSubmit={handleSubmit} noValidate>

            <p className="modal-section-label">Your Details</p>
            <p className="modal-hint" style={{ marginBottom: "16px" }}>
              Pre-filled from your profile — edit anything before submitting.
            </p>

            <div className="modal-row-2">
              <div className="modal-field">
                <label className="modal-label">Full Name <span className="modal-required">*</span></label>
                <input className="modal-input" name="name" value={form.name} onChange={handleChange} required />
              </div>
              <div className="modal-field">
                <label className="modal-label">Email <span className="modal-required">*</span></label>
                <input className="modal-input" name="email" type="email" value={form.email} onChange={handleChange} required />
              </div>
            </div>

            <div className="modal-row-2">
              <div className="modal-field">
                <label className="modal-label">Phone</label>
                <input className="modal-input" name="phone" value={form.phone} onChange={handleChange} placeholder="Optional" />
              </div>
              <div className="modal-field">
                <label className="modal-label">Experience (years) <span className="modal-required">*</span></label>
                <input className="modal-input" name="experience" type="number" min="0" max="50" value={form.experience} onChange={handleChange} />
              </div>
            </div>

            <div className="modal-field">
              <label className="modal-label">Resume URL</label>
              <input className="modal-input" name="resume_url" value={form.resume_url} onChange={handleChange} placeholder="https://drive.google.com/..." />
            </div>

            <div className="modal-divider" style={{ margin: "18px 0" }} />
            <p className="modal-section-label">Links &amp; Motivation</p>

            <div className="modal-row-2">
              <div className="modal-field">
                <label className="modal-label">LinkedIn</label>
                <input className="modal-input" name="linkedin" value={form.linkedin} onChange={handleChange} placeholder="https://linkedin.com/in/..." />
              </div>
            </div>

            <div className="modal-field">
              <label className="modal-label">
                Why are you interested in this role? <span className="modal-required">*</span>
              </label>
              <textarea
                className="modal-input modal-textarea"
                name="why_interested"
                value={form.why_interested}
                onChange={handleChange}
                placeholder="Briefly describe what excites you about this position…"
                rows={4}
                required
              />
            </div>

            {errorMsg && <p className="modal-error">{errorMsg}</p>}

            <div className="modal-footer">
              <button type="button" className="modal-btn-cancel" onClick={onClose} disabled={step === "submitting"}>
                Cancel
              </button>
              <button type="submit" className="modal-btn-primary" disabled={step === "submitting"}>
                {step === "submitting" ? (
                  <><span className="modal-btn-spinner" /> Submitting…</>
                ) : (
                  "Submit Application"
                )}
              </button>
            </div>

          </form>
        )}

      </div>
    </div>
  );
}

export default ApplyModal;