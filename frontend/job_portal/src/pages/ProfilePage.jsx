import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Select from "react-select";
import "./ProfilePage.css";
import Logout from "../components/auth/Logout";
import Loader from "../components/loader";
import api from "../api/axios";

export default function Profile() {
  const navigate = useNavigate();

  const personalRef = useRef(null);
  const prefRef = useRef(null);
  const securityRef = useRef(null);

  const [active, setActive] = useState("personal");
  const [role, setRole] = useState("jobseeker");
  const [loading, setLoading] = useState(true);

  // ── Personal Info ──────────────────────────────────────────────
  const [profile, setProfile] = useState({ name: "", email: "", phone: "" });
  const [personalEdit, setPersonalEdit] = useState(false);
  const [personalForm, setPersonalForm] = useState({ fullname: "", phone: "" });
  const [personalSaving, setPersonalSaving] = useState(false);
  const [personalError, setPersonalError] = useState("");
  const [personalSuccess, setPersonalSuccess] = useState(false);

  // ── Job Preferences ────────────────────────────────────────────
  const [locationOptions, setLocationOptions] = useState([]);
  const [domainOptions, setDomainOptions] = useState([]);
  const [prefEdit, setPrefEdit] = useState(false);
  const [prefForm, setPrefForm] = useState({
    location_ids: [],
    preferred_domain_id: null,
    experience: "",
  });
  const [savedPrefForm, setSavedPrefForm] = useState({
    location_ids: [],
    preferred_domain_id: null,
    experience: "",
  });
  const [prefSaving, setPrefSaving] = useState(false);
  const [prefError, setPrefError] = useState("");
  const [prefSuccess, setPrefSuccess] = useState(false);

  // ── Company Info ───────────────────────────────────────────────
  const [companyEdit, setCompanyEdit] = useState(false);
  const [companyForm, setCompanyForm] = useState({
    company_name: "",
    website: "",
    description: "",
  });
  const [savedCompanyForm, setSavedCompanyForm] = useState({
    company_name: "",
    website: "",
    description: "",
  });
  const [companySaving, setCompanySaving] = useState(false);
  const [companyError, setCompanyError] = useState("");
  const [companySuccess, setCompanySuccess] = useState(false);

  // ── Security ───────────────────────────────────────────────────
  const [securityEdit, setSecurityEdit] = useState(false);
  const [securityForm, setSecurityForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [securitySaving, setSecuritySaving] = useState(false);
  const [securityError, setSecurityError] = useState("");
  const [securitySuccess, setSecuritySuccess] = useState(false);

  // ── Resume ─────────────────────────────────────────────────────
  const [hasResume, setHasResume] = useState(false);
  const [resumeUploading, setResumeUploading] = useState(false);
  const [resumeProcessing, setResumeProcessing] = useState(false);
  const [resumeDeleting, setResumeDeleting] = useState(false);
  const [resumeViewing, setResumeViewing] = useState(false);
  const [resumeError, setResumeError] = useState("");
  const [resumeSuccess, setResumeSuccess] = useState("");
  const fileInputRef = useRef(null);

  // ── Scroll helpers ─────────────────────────────────────────────
  const scrollToSection = (ref) => ref.current?.scrollIntoView({ behavior: "smooth" });
  const handleScroll = (section, ref) => {
    setActive(section);
    scrollToSection(ref);
  };

  // ── Fetch all data on mount ────────────────────────────────────
  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [profileRes, locRes, domainRes] = await Promise.all([
          api.get("/profile/details"),
          api.get("/jobs/locations"),
          api.get("/jobs/industry-domains"),
        ]);

        const data = profileRes.data;
        setRole(data.user_role);
        setProfile({ name: data.fullname, email: data.email, phone: data.phone ?? "" });
        setPersonalForm({ fullname: data.fullname, phone: data.phone ?? "" });

        setLocationOptions(locRes.data.map((l) => ({ value: l.id, label: l.name })));
        setDomainOptions(domainRes.data.map((d) => ({ value: d.id, label: d.name })));

        if (data.user_role === "jobseeker" && data.jobseeker_details) {
          const js = data.jobseeker_details;
          const initial = {
            location_ids: js.preferred_locations?.map((l) => l.id) ?? [],
            preferred_domain_id: js.preferred_domain?.id ?? null,
            experience: js.experience ?? "",
          };
          setPrefForm(initial);
          setSavedPrefForm({ ...initial, location_ids: [...initial.location_ids] });

          // ── Fetch resume status only for jobseekers ──
          try {
            const resumeRes = await api.get("/resume/status");
            setHasResume(resumeRes.data.has_resume);
          } catch {
            setHasResume(false);
          }
        }

        if (data.user_role === "recruiter" && data.recruiter_details) {
          const rc = data.recruiter_details;
          const initial = {
            company_name: rc.company_name ?? "",
            website: rc.website ?? "",
            description: rc.description ?? "",
          };
          setCompanyForm(initial);
          setSavedCompanyForm({ ...initial });
        }
      } catch (err) {
        console.error("Failed to load profile:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  // ── Save Personal ──────────────────────────────────────────────
  const savePersonal = async () => {
    setPersonalSaving(true);
    setPersonalError("");
    const phoneVal = personalForm.phone?.trim() || null;
    try {
      await api.patch("/profile/personal", {
        fullname: personalForm.fullname,
        phone: phoneVal,
      });
      setProfile((prev) => ({
        ...prev,
        name: personalForm.fullname,
        phone: phoneVal ?? "",
      }));
      setPersonalEdit(false);
      setPersonalSuccess(true);
      setTimeout(() => setPersonalSuccess(false), 3000);
    } catch (err) {
      const d1 = err.response?.data?.detail;
      setPersonalError(
        Array.isArray(d1)
          ? d1.map((e) => e.msg.replace("Value error, ", "")).join(" • ")
          : (d1 ?? "Failed to update personal info.")
      );
    } finally {
      setPersonalSaving(false);
    }
  };

  const cancelPersonal = () => {
    setPersonalForm({ fullname: profile.name, phone: profile.phone });
    setPersonalError("");
    setPersonalEdit(false);
  };

  // ── Save Preferences ───────────────────────────────────────────
  const savePreferences = async () => {
    setPrefSaving(true);
    setPrefError("");
    try {
      await api.patch("/profile/preferences", {
        location_ids: prefForm.location_ids,
        preferred_domain_id: prefForm.preferred_domain_id,
        experience: prefForm.experience !== "" ? Number(prefForm.experience) : null,
      });
      setSavedPrefForm({ ...prefForm, location_ids: [...prefForm.location_ids] });
      setPrefEdit(false);
      setPrefSuccess(true);
      setTimeout(() => setPrefSuccess(false), 3000);
    } catch (err) {
      const d2 = err.response?.data?.detail;
      setPrefError(
        Array.isArray(d2)
          ? d2.map((e) => e.msg.replace("Value error, ", "")).join(" • ")
          : (d2 ?? "Failed to update preferences.")
      );
    } finally {
      setPrefSaving(false);
    }
  };

  const cancelPreferences = () => {
    setPrefForm(savedPrefForm);
    setPrefError("");
    setPrefEdit(false);
  };

  // ── Save Company ───────────────────────────────────────────────
  const saveCompany = async () => {
    setCompanySaving(true);
    setCompanyError("");
    try {
      await api.patch("/profile/company", {
        ...companyForm,
        website: companyForm.website?.trim() || null,
      });
      setSavedCompanyForm({ ...companyForm });
      setCompanyEdit(false);
      setCompanySuccess(true);
      setTimeout(() => setCompanySuccess(false), 3000);
    } catch (err) {
      const d3 = err.response?.data?.detail;
      setCompanyError(
        Array.isArray(d3)
          ? d3.map((e) => e.msg.replace("Value error, ", "")).join(" . ")
          : (d3 ?? "Failed to update company info.")
      );
    } finally {
      setCompanySaving(false);
    }
  };

  const cancelCompany = () => {
    setCompanyForm(savedCompanyForm);
    setCompanyError("");
    setCompanyEdit(false);
  };

  // ── Save Security ──────────────────────────────────────────────
  const saveSecurity = async () => {
    setSecurityError("");

    if (!securityForm.currentPassword) {
      setSecurityError("Please enter your current password.");
      return;
    }
    if (!securityForm.newPassword) {
      setSecurityError("Please enter a new password.");
      return;
    }
    if (securityForm.newPassword !== securityForm.confirmPassword) {
      setSecurityError("New passwords do not match.");
      return;
    }

    setSecuritySaving(true);
    try {
      await api.patch("/profile/change-password", {
        current_pass: securityForm.currentPassword,
        new_pass: securityForm.newPassword,
        confirm_pass: securityForm.confirmPassword,
      });
      setSecurityForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
      setSecurityEdit(false);
      setSecuritySuccess(true);
      setTimeout(() => setSecuritySuccess(false), 3000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setSecurityError(
        Array.isArray(detail)
          ? detail.map((e) => e.msg.replace("Value error, ", "")).join(" • ")
          : (detail ?? "Failed to update password.")
      );
    } finally {
      setSecuritySaving(false);
    }
  };

  const cancelSecurity = () => {
    setSecurityForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
    setSecurityError("");
    setSecurityEdit(false);
  };

  // ── Resume Handlers ────────────────────────────────────────────
  const handleResumeUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setResumeError("Only PDF files are allowed.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setResumeError("File size must be under 5MB.");
      return;
    }

    setResumeUploading(true);
    setResumeProcessing(false);
    setResumeError("");
    setResumeSuccess("");

    const formData = new FormData();
    formData.append("file", file);

    // After 800ms assume file is saved, now embedding pipeline is running
    const processingTimer = setTimeout(() => setResumeProcessing(true), 800);

    try {
      await api.post("/resume/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setHasResume(true);
      setResumeSuccess("Resume uploaded successfully.");
      setTimeout(() => setResumeSuccess(""), 3000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setResumeError(
        Array.isArray(detail)
          ? detail.map((e) => e.msg.replace("Value error, ", "")).join(" • ")
          : (detail ?? "Upload failed. Please try again.")
      );
    } finally {
      clearTimeout(processingTimer);
      setResumeUploading(false);
      setResumeProcessing(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleResumeDelete = async () => {
    if (!window.confirm("Delete your resume? This cannot be undone.")) return;

    setResumeDeleting(true);
    setResumeError("");
    setResumeSuccess("");

    try {
      await api.delete("/resume/delete");
      setHasResume(false);
      setResumeSuccess("Resume deleted.");
      setTimeout(() => setResumeSuccess(""), 3000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setResumeError(detail ?? "Delete failed. Please try again.");
    } finally {
      setResumeDeleting(false);
    }
  };

  const handleResumeView = async () => {
    setResumeViewing(true);
    setResumeError("");
    try {
      // Fetch as blob — keeps auth header, avoids window.open auth bypass
      const res = await api.get("/resume/view", { responseType: "blob" });
      const blobUrl = URL.createObjectURL(res.data);
      window.open(blobUrl, "_blank");
      setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);
    } catch (err) {
      setResumeError("Could not load resume. Please try again.");
    } finally {
      setResumeViewing(false);
    }
  };

  // ── Derived Select values ──────────────────────────────────────
  const selectedLocations = locationOptions.filter((o) =>
    prefForm.location_ids.includes(o.value)
  );
  const selectedDomain =
    domainOptions.find((o) => o.value === prefForm.preferred_domain_id) ?? null;

  if (loading) {
    return <Loader />;
  }

  return (
    <div className="profile-page">

      {/* Top Bar */}
      <div className="top-bar">
        <button
          className="dashboard-btn"
          onClick={() => navigate(role === "jobseeker" ? "/joblist" : "/recruiter-dashboard")}
        >
          {role === "jobseeker" ? "Jobs" : "Dashboard"}
        </button>
        <Logout />
      </div>

      <div className="page-body">

        {/* Sidebar */}
        <div className="sidebar">
          <div className="sidebar-profile-mini">
            <div className="avatar-lg">
              <span>{profile.name?.charAt(0)?.toUpperCase() || "U"}</span>
            </div>
            <p className="sidebar-name">{profile.name}</p>
            <p className="sidebar-role">{role === "jobseeker" ? "Job Seeker" : "Recruiter"}</p>
          </div>
          <nav className="sidebar-nav">
            <button
              className={`nav-item ${active === "personal" ? "nav-active" : ""}`}
              onClick={() => handleScroll("personal", personalRef)}
            >
              Personal Info
            </button>
            <button
              className={`nav-item ${active === "preferences" ? "nav-active" : ""}`}
              onClick={() => handleScroll("preferences", prefRef)}
            >
              {role === "jobseeker" ? "Preferences" : "Company Info"}
            </button>
            <button
              className={`nav-item ${active === "security" ? "nav-active" : ""}`}
              onClick={() => handleScroll("security", securityRef)}
            >
              Security
            </button>
          </nav>
        </div>

        {/* Main Content */}
        <div className="main-content">

          {/* ── Personal Info Card ── */}
          <div ref={personalRef} className="card">
            <div className="card-header">
              <div className="card-title-group">
                <h3 className="card-title">Personal Information</h3>
                <p className="card-subtitle">
                  {personalEdit ? "Update your name and phone number" : "Your basic profile details"}
                </p>
              </div>
              {!personalEdit && (
                <button className="edit-btn" onClick={() => setPersonalEdit(true)}>
                  Edit Profile
                </button>
              )}
            </div>

            <div className="card-divider" />

            {!personalEdit && (
              <div className="info-grid">
                <div className="info-field">
                  <span className="field-label">Full Name</span>
                  <span className="field-value">{profile.name || "—"}</span>
                </div>
                <div className="info-field">
                  <span className="field-label">Email Address</span>
                  <span className="field-value field-muted">{profile.email}</span>
                </div>
                <div className="info-field">
                  <span className="field-label">Phone Number</span>
                  <span className="field-value">{profile.phone || "—"}</span>
                </div>
              </div>
            )}

            {personalEdit && (
              <div className="edit-section">
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Full Name</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Enter your full name"
                      value={personalForm.fullname}
                      onChange={(e) =>
                        setPersonalForm({ ...personalForm, fullname: e.target.value })
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Email Address</label>
                    <input
                      type="text"
                      className="form-input form-input--disabled"
                      value={profile.email}
                      disabled
                    />
                    <span className="field-hint">Email cannot be changed</span>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Phone Number</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="+919876543210"
                      value={personalForm.phone}
                      onChange={(e) =>
                        setPersonalForm({ ...personalForm, phone: e.target.value })
                      }
                    />
                    <span className="field-hint">
                      Format: +[country code][number] — e.g. +919876543210
                    </span>
                  </div>
                </div>

                {personalError && <p className="msg msg--error">{personalError}</p>}

                <div className="action-bar">
                  <button className="btn-save" onClick={savePersonal} disabled={personalSaving}>
                    {personalSaving ? <><span className="btn-spinner" /> Saving…</> : "Save Changes"}
                  </button>
                  <button className="btn-cancel" onClick={cancelPersonal}>
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {personalSuccess && (
              <p className="msg msg--success">Personal info updated successfully</p>
            )}
          </div>

          {/* ── Job Preferences Card (jobseeker) ── */}
          {role === "jobseeker" && (
            <div ref={prefRef} className="card">
              <div className="card-header">
                <div className="card-title-group">
                  <h3 className="card-title">Job Preferences</h3>
                  <p className="card-subtitle">
                    {prefEdit
                      ? "Update your job search preferences"
                      : "Your current job search settings"}
                  </p>
                </div>
                {!prefEdit && (
                  <button className="edit-btn" onClick={() => setPrefEdit(true)}>
                    Edit
                  </button>
                )}
              </div>

              <div className="card-divider" />

              <div className="preferences-grid">
                <div className="pref-field">
                  <label className="form-label">Preferred Locations</label>
                  <Select
                    options={locationOptions}
                    isMulti
                    isDisabled={!prefEdit}
                    placeholder="Search & select locations…"
                    value={selectedLocations}
                    onChange={(selected) =>
                      setPrefForm({
                        ...prefForm,
                        location_ids: selected ? selected.map((s) => s.value) : [],
                      })
                    }
                    className="react-select-container"
                    classNamePrefix="rselect"
                  />
                </div>

                <div className="pref-field">
                  <label className="form-label">Industry Domain</label>
                  <Select
                    options={domainOptions}
                    isDisabled={!prefEdit}
                    placeholder="Select domain…"
                    value={selectedDomain}
                    onChange={(selected) =>
                      setPrefForm({
                        ...prefForm,
                        preferred_domain_id: selected ? selected.value : null,
                      })
                    }
                    className="react-select-container"
                    classNamePrefix="rselect"
                  />
                </div>

                <div className="pref-field">
                  <label className="form-label">Years of Experience</label>
                  <select
                    className={`form-select ${!prefEdit ? "form-select--disabled" : ""}`}
                    disabled={!prefEdit}
                    value={prefForm.experience}
                    onChange={(e) =>
                      setPrefForm({ ...prefForm, experience: e.target.value })
                    }
                  >
                    <option value="">Select experience…</option>
                    {Array.from({ length: 31 }, (_, i) => (
                      <option key={i} value={i}>
                        {i === 0 ? "Fresher (0 years)" : `${i} year${i > 1 ? "s" : ""}`}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {prefError && <p className="msg msg--error">{prefError}</p>}

              {prefEdit && (
                <div className="action-bar">
                  <button className="btn-save" onClick={savePreferences} disabled={prefSaving}>
                    {prefSaving ? <><span className="btn-spinner" /> Saving…</> : "Save Changes"}
                  </button>
                  <button className="btn-cancel" onClick={cancelPreferences}>
                    Cancel
                  </button>
                </div>
              )}

              {prefSuccess && (
                <p className="msg msg--success">Preferences updated successfully</p>
              )}

              {/* ── Resume Section ── */}
              <div className="card-divider" style={{ marginTop: "24px" }} />

              <div className="upload-zone">
                <div className="upload-zone-header">
                  <p className="upload-title">Resume</p>
                  {hasResume && (
                    <span className="resume-badge">Uploaded</span>
                  )}
                </div>

                {hasResume ? (
                  <div className="resume-existing">
                    <div className="resume-file-row">
                      <span className="resume-filename">📄 resume.pdf</span>
                    </div>
                    <div className="resume-actions">
                      <button
                        className="btn-upload"
                        onClick={handleResumeView}
                        disabled={resumeViewing || resumeUploading || resumeDeleting}
                      >
                        {resumeViewing ? "Opening…" : "View"}
                      </button>
                      <button
                        className="btn-upload"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={resumeViewing || resumeUploading || resumeDeleting}
                      >
                        {resumeUploading
                          ? resumeProcessing
                            ? "Processing…"
                            : "Uploading…"
                          : "Replace"}
                      </button>
                      <button
                        className="btn-cancel"
                        onClick={handleResumeDelete}
                        disabled={resumeViewing || resumeUploading || resumeDeleting}
                      >
                        {resumeDeleting ? "Deleting…" : "Delete"}
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="upload-desc">PDF format, max 5MB</p>
                    <button
                      className="btn-upload"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={resumeUploading}
                    >
                      {resumeUploading
                        ? resumeProcessing
                          ? "Processing…"
                          : "Uploading…"
                        : "Browse Files"}
                    </button>
                  </>
                )}

                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  style={{ display: "none" }}
                  onChange={handleResumeUpload}
                />

                {resumeError   && <p className="msg msg--error">{resumeError}</p>}
                {resumeSuccess && <p className="msg msg--success">{resumeSuccess}</p>}
              </div>
            </div>
          )}

          {/* ── Company Info Card (recruiter) ── */}
          {role === "recruiter" && (
            <div ref={prefRef} className="card">
              <div className="card-header">
                <div className="card-title-group">
                  <h3 className="card-title">Company Information</h3>
                  <p className="card-subtitle">
                    {companyEdit ? "Update your company details" : "Your company profile"}
                  </p>
                </div>
                {!companyEdit && (
                  <button className="edit-btn" onClick={() => setCompanyEdit(true)}>
                    Edit
                  </button>
                )}
              </div>

              <div className="card-divider" />

              {!companyEdit && (
                <div className="info-grid">
                  <div className="info-field">
                    <span className="field-label">Company Name</span>
                    <span className="field-value">{savedCompanyForm.company_name || "—"}</span>
                  </div>
                  <div className="info-field">
                    <span className="field-label">Website</span>
                    <span className="field-value">{savedCompanyForm.website || "—"}</span>
                  </div>
                  <div className="info-field info-field--full">
                    <span className="field-label">Description</span>
                    <span className="field-value">{savedCompanyForm.description || "—"}</span>
                  </div>
                </div>
              )}

              {companyEdit && (
                <div className="edit-section">
                  <div className="form-row form-row--2col">
                    <div className="form-group">
                      <label className="form-label">Company Name</label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="Enter company name"
                        value={companyForm.company_name}
                        onChange={(e) =>
                          setCompanyForm({ ...companyForm, company_name: e.target.value })
                        }
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Website</label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="https://yourcompany.com"
                        value={companyForm.website}
                        onChange={(e) =>
                          setCompanyForm({ ...companyForm, website: e.target.value })
                        }
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Description</label>
                    <textarea
                      className="form-textarea"
                      placeholder="Tell job seekers about your company…"
                      value={companyForm.description}
                      onChange={(e) =>
                        setCompanyForm({ ...companyForm, description: e.target.value })
                      }
                    />
                  </div>

                  {companyError && <p className="msg msg--error">{companyError}</p>}

                  <div className="action-bar">
                    <button className="btn-save" onClick={saveCompany} disabled={companySaving}>
                      {companySaving ? <><span className="btn-spinner" /> Saving…</> : "Save Changes"}
                    </button>
                    <button className="btn-cancel" onClick={cancelCompany}>
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {companySuccess && (
                <p className="msg msg--success">Company info updated successfully</p>
              )}
            </div>
          )}

          {/* ── Security Card ── */}
          <div ref={securityRef} className="card">
            <div className="card-header">
              <div className="card-title-group">
                <h3 className="card-title">Security & Password</h3>
                <p className="card-subtitle">
                  {securityEdit
                    ? "Enter your current and new password"
                    : "Manage your account password"}
                </p>
              </div>
              {!securityEdit && (
                <button className="edit-btn" onClick={() => setSecurityEdit(true)}>
                  Change Password
                </button>
              )}
            </div>

            <div className="card-divider" />

            {!securityEdit && (
              <div className="security-placeholder">
                <p className="security-text">Your password is set and secure.</p>
                <p className="security-hint">Click "Change Password" to update it.</p>
              </div>
            )}

            {securityEdit && (
              <div className="edit-section">
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Current Password</label>
                    <input
                      type="password"
                      className="form-input"
                      placeholder="Enter current password"
                      value={securityForm.currentPassword}
                      onChange={(e) =>
                        setSecurityForm({ ...securityForm, currentPassword: e.target.value })
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">New Password</label>
                    <input
                      type="password"
                      className="form-input"
                      placeholder="Enter new password"
                      value={securityForm.newPassword}
                      onChange={(e) =>
                        setSecurityForm({ ...securityForm, newPassword: e.target.value })
                      }
                    />
                    <span className="field-hint">
                      Min 8 chars with uppercase, lowercase, number & special character (@$!%*?&)
                    </span>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Confirm New Password</label>
                    <input
                      type="password"
                      className="form-input"
                      placeholder="Re-enter new password"
                      value={securityForm.confirmPassword}
                      onChange={(e) =>
                        setSecurityForm({ ...securityForm, confirmPassword: e.target.value })
                      }
                    />
                  </div>
                </div>

                {securityError && <p className="msg msg--error">{securityError}</p>}

                <div className="action-bar">
                  <button className="btn-save" onClick={saveSecurity} disabled={securitySaving}>
                    {securitySaving ? <><span className="btn-spinner" /> Updating…</> : "Update Password"}
                  </button>
                  <button className="btn-cancel" onClick={cancelSecurity}>
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {securitySuccess && (
              <p className="msg msg--success">Password updated successfully</p>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}