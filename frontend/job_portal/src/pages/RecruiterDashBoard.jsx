import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./RecruiterDashBoard.css";
import JobPostCard from "../components/JobPostCard";
import Logout from "../components/auth/Logout";
import Loader from "../components/loader";
import { FaPlus, FaBriefcase } from "react-icons/fa";
import axios from "axios";
import Select from "react-select";
 
const API_BASE = "http://127.0.0.1:8000";
 
const RecruiterDashBoard = () => {
  const navigate = useNavigate();
  const [expandedJobId, setExpandedJobId] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [locations, setLocations] = useState([]);
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
 
  const [formData, setFormData] = useState({
    company_name: "",
    job_title: "",
    location_ids: [],
    industry_domain_id: "",
    min_experience: "",
    job_description: "",
  });
 
  const token = localStorage.getItem("token");
 
  useEffect(() => {
    fetchLocations();
    fetchDomains();
    fetchJobs();
  }, []);
 
  const fetchLocations = async () => {
    const res = await axios.get(`${API_BASE}/jobs/locations`);
    setLocations(res.data);
  };
 
  const fetchDomains = async () => {
    const res = await axios.get(`${API_BASE}/jobs/industry-domains`);
    setDomains(res.data);
  };
 
  const fetchJobs = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API_BASE}/jobs/postedjobs`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setJobs(res.data);
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
 
    if (formData.location_ids.length === 0) {
      alert("Please select at least one location.");
      return;
    }
    if (!formData.company_name || !formData.job_title) {
      alert("Please fill all required fields.");
      return;
    }
    if (formData.min_experience === "") {
      alert("Please select minimum experience.");
      return;
    }
    if (formData.industry_domain_id === "") {
      alert("Please select industry domain.");
      return;
    }
 
    try {
      setLoading(true);
      await axios.post(
        `${API_BASE}/jobs/post`,
        {
          ...formData,
          industry_domain_id: Number(formData.industry_domain_id),
          min_experience: Number(formData.min_experience),
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
 
      setFormData({
        company_name: "",
        job_title: "",
        location_ids: [],
        industry_domain_id: "",
        min_experience: "",
        job_description: "",
      });
 
      await fetchJobs();
      setSubmitSuccess(true);
      setTimeout(() => setSubmitSuccess(false), 3000);
    } catch (err) {
      alert("Failed to post job");
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
      await axios.delete(`${API_BASE}/jobs/${job_id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setJobs((prev) => prev.filter((job) => job.job_id !== job_id));
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
                
                <><FaPlus style={{ fontSize: 12 }} /> Publish Job Posting</>
                
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