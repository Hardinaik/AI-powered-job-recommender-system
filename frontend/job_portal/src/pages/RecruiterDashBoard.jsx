import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./RecruiterDashBoard.css";
import JobPostCard from "../components/JobPostCard";
import Logout from "../components/auth/Logout";
import Loader from "../components/loader";
import { FaPlus } from "react-icons/fa";
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
    const ids = selectedOptions
      ? selectedOptions.map((option) => option.value)
      : [];

    setFormData({ ...formData, location_ids: ids });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // manual validation (react-select)
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
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      // reset form
      setFormData({
        company_name: "",
        job_title: "",
        location_ids: [],
        industry_domain_id: "",
        min_experience: "",
        job_description: "",
      });

      await fetchJobs();

      alert("Job successfully posted!");
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
    <div className="page-container">
      {loading && <Loader />}

      <div className="top-bar">
        <button 
          className="profile-btn" 
          onClick={() => navigate("/profile")}
        >
          Profile
        </button>
        <Logout />
      </div>

      <div className="workspace-container">
        <h1 className="workspace-title">Recruiter Workspace</h1>

        <div className="workspace-grid">

          {/* FORM */}
          <form className="post-job-card" onSubmit={handleSubmit}>
            <h2>
              <FaPlus className="icon-blue" /> Post a New Job
            </h2>

            

            <label className="required">Company Name</label>
            <input
              type="text"
              name="company_name"
              value={formData.company_name}
              onChange={handleChange}
              required
            />

            <label className="required">Industry Domain</label>
            <select
              name="industry_domain_id"
              value={formData.industry_domain_id}
              onChange={handleChange}
              required
            >
              <option value="" disabled>
                Select Domain
              </option>
              {domains.map((domain) => (
                <option key={domain.id} value={domain.id}>
                  {domain.name}
                </option>
              ))}
            </select>

            <label className="required">Job Title</label>
            <input
              type="text"
              name="job_title"
              value={formData.job_title}
              onChange={handleChange}
              required
            />

            <label className="required">Locations</label>
            <Select
              options={locationOptions}
              isMulti
              placeholder="Search & select locations..."
              value={locationOptions.filter((option) =>
                formData.location_ids.includes(option.value)
              )}
              onChange={handleLocationChange}
            />

            <label className="required">
              Minimum Required Experience (Years)
            </label>
            <select
              name="min_experience"
              value={formData.min_experience}
              onChange={handleChange}
              required
            >
              <option value="" disabled>
                Select Experience
              </option>
              {[...Array(31).keys()].map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>

            <label className="required">Job Description</label>
            <textarea
              name="job_description"
              value={formData.job_description}
              onChange={handleChange}
              required
            />

            <button
              type="submit"
              className="publish-btn"
              disabled={loading}
            >
              Publish Job Posting
            </button>
          </form>

          {/* JOB LIST */}
          <div className="jobs-section">
            <h2 className="job-post-title">Your Posted Jobs</h2>

            {jobs.length === 0 ? (
              <p className="info-text">No jobs posted yet.</p>
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