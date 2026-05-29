/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./RecruiterDashBoard.css";
import JobPostCard from "../components/JobPostCard";
import Logout from "../components/auth/Logout";
import Loader from "../components/loader";
import ErrorBanner from "../components/ErrorBanner";
import { getErrorMessage } from "../utils/errorUtils";
import { FaPlus, FaBriefcase } from "react-icons/fa";
import Select from "react-select";
import api from "../api/axios";



const RecruiterDashBoard = () => {
  const navigate = useNavigate();
  const [expandedJobId, setExpandedJobId] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [locations, setLocations] = useState([]);
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    company_name: "",
    job_title: "",
    location_ids: [],
    industry_domain_id: "",
    min_experience: "",
    max_experience: "",
    job_description: "",
  });

  useEffect(() => {
    fetchLocations();
    fetchDomains();
    fetchJobs();
  }, []);

  const fetchLocations = async () => {
    try {
      const res = await api.get("/jobs/locations");
      setLocations(res.data);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const fetchDomains = async () => {
      try {
        const res = await api.get("/jobs/industry-domains");
        setDomains(res.data);
      } catch (err) {
        setError(getErrorMessage(err));
      }
    };

    const fetchJobs = async () => {
    try {
      setLoading(true);
      const res = await api.get("/jobs/postedjobs");
      setJobs(res.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleLocationChange = (selectedOptions) => {
    const ids = selectedOptions ? selectedOptions.map((o) => o.value) : [];
    setFormData({ ...formData, location_ids: ids });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.company_name || !formData.job_title) {
      setError("Please fill in company name and job title.");
      return;
    }
    if (formData.location_ids.length === 0) {
      setError("Please select at least one location.");
      return;
    }
    if (formData.industry_domain_id === "") {
      setError("Please select an industry domain.");
      return;
    }
    if (formData.min_experience === "") {
      setError("Please select minimum experience.");
      return;
    }
    if (formData.max_experience === "") {
      setError("Please select maximum experience.");
      return;
    }
    if (Number(formData.max_experience) < Number(formData.min_experience)) {
      setError("Maximum experience must be ≥ minimum experience.");
      return;
    }

    try {
      setLoading(true);
      
      await api.post("/jobs/post", {
        ...formData,
        industry_domain_id: Number(formData.industry_domain_id),
        min_experience: Number(formData.min_experience),
        max_experience: Number(formData.max_experience),
      });

      setFormData({
        company_name: "",
        job_title: "",
        location_ids: [],
        industry_domain_id: "",
        min_experience: "",
        max_experience: "",
        job_description: "",
      });

      await fetchJobs();
      setSubmitSuccess(true);
      setTimeout(() => setSubmitSuccess(false), 3000);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const toggleDetails = (job_id) => {
    setExpandedJobId(expandedJobId === job_id ? null : job_id);
  };

  const deleteJob = async (job_id) => {
    try {
      setLoading(true);
      await api.delete(`/jobs/${job_id}`);
      setJobs((prev) => prev.filter((job) => job.job_id !== job_id));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const locationOptions = locations.map((loc) => ({
    value: loc.id,
    label: loc.name,
  }));

  return (
    <div className="rd-page">
      {loading && <Loader />}

      {/* Top Bar */}
      <div className="rd-topbar">
        <div className="rd-topbar-brand">
          <span className="rd-brand-dot" />
          <span className="rd-brand-name">Recruiter Workspace</span>
        </div>
        <div className="rd-topbar-actions">
          <button className="rd-profile-btn" onClick={() => navigate("/profile")}>
            Profile
          </button>
          <Logout />
        </div>
      </div>

      {/* Body */}
      <ErrorBanner message={error} onClose={() => setError(null)} />
      <div className="rd-body">
        

        {/* Left — Post Job Form */}
        <div className="rd-form-col">
          <div className="rd-card">
            <div className="rd-card-header">
              <div className="rd-card-title-group">
                <h2 className="rd-card-title">Post a New Job</h2>
                <p className="rd-card-subtitle">Fill in the details to publish a listing</p>
              </div>
              <span className="rd-post-icon"><FaPlus /></span>
            </div>
            <div className="rd-card-divider" />

            <form onSubmit={handleSubmit} className="rd-form">

              <div className="rd-form-row">
                <div className="rd-form-group">
                  <label className="rd-label rd-required">Company Name</label>
                  <input
                    className="rd-input"
                    type="text"
                    name="company_name"
                    placeholder="e.g. Acme Corp"
                    value={formData.company_name}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="rd-form-group">
                  <label className="rd-label rd-required">Job Title</label>
                  <input
                    className="rd-input"
                    type="text"
                    name="job_title"
                    placeholder="e.g. Senior React Developer"
                    value={formData.job_title}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="rd-form-row">
                <div className="rd-form-group">
                  <label className="rd-label rd-required">Industry Domain</label>
                  <select
                    className="rd-select"
                    name="industry_domain_id"
                    value={formData.industry_domain_id}
                    onChange={handleChange}
                    required
                  >
                    <option value="" disabled>Select domain…</option>
                    {domains.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>

                <div className="rd-form-group">
                  <label className="rd-label rd-required">Locations</label>
                  <Select
                    options={locationOptions}
                    isMulti
                    placeholder="Search & select locations…"
                    value={locationOptions.filter((o) =>
                      formData.location_ids.includes(o.value)
                    )}
                    onChange={handleLocationChange}
                    className="rd-react-select"
                    classNamePrefix="rdsel"
                  />
                </div>
              </div>

              <div className="rd-form-row">
                <div className="rd-form-group">
                  <label className="rd-label rd-required">Min. Experience (Years)</label>
                  <select
                    className="rd-select"
                    name="min_experience"
                    value={formData.min_experience}
                    onChange={handleChange}
                    required
                  >
                    <option value="" disabled>Select experience…</option>
                    {[...Array(31).keys()].map((y) => (
                      <option key={y} value={y}>
                        {y === 0 ? "Fresher (0 years)" : `${y} year${y > 1 ? "s" : ""}`}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="rd-form-group">
                  <label className="rd-label rd-required">Max. Experience (Years)</label>
                  <select
                    className="rd-select"
                    name="max_experience"
                    value={formData.max_experience}
                    onChange={handleChange}
                    required
                  >
                    <option value="" disabled>Select experience…</option>
                    {[...Array(31).keys()].map((y) => (
                      <option key={y} value={y}>
                        {y === 0 ? "Fresher (0 years)" : `${y} year${y > 1 ? "s" : ""}`}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="rd-form-group">
                <label className="rd-label rd-required">Job Description</label>
                <textarea
                  className="rd-textarea"
                  name="job_description"
                  placeholder="Describe the role, responsibilities, requirements…"
                  value={formData.job_description}
                  onChange={handleChange}
                  required
                />
              </div>

              {submitSuccess && (
                <p className="rd-msg rd-msg--success">✓ Job posted successfully!</p>
              )}

              <button
                type="submit"
                className="rd-publish-btn"
                disabled={loading}
              >
                <FaPlus style={{ fontSize: 12 }} /> Publish Job Posting
              </button>

            </form>
          </div>
        </div>

        {/* Right — Job Listings */}
        <div className="rd-jobs-col">
          <div className="rd-jobs-header">
            <div>
              <h3 className="rd-jobs-title">Your Posted Jobs</h3>
              <p className="rd-jobs-subtitle">
                {jobs.length === 0
                  ? "No listings yet"
                  : `${jobs.length} active listing${jobs.length > 1 ? "s" : ""}`}
              </p>
            </div>
            <span className="rd-jobs-badge">
              <FaBriefcase style={{ fontSize: 13 }} />
              {jobs.length}
            </span>
          </div>

          <div className="rd-jobs-list">
            {jobs.length === 0 ? (
              <div className="rd-empty-state">
                <p className="rd-empty-title">No jobs posted yet</p>
                <p className="rd-empty-hint">Use the form to publish your first listing.</p>
              </div>
            ) : (
              jobs.map((job) => (
                <JobPostCard
                  key={job.job_id}
                  job={job}
                  isExpanded={expandedJobId === job.job_id}
                  onToggle={toggleDetails}
                  onDelete={deleteJob}
                />
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default RecruiterDashBoard;