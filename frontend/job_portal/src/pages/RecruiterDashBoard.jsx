import React, { useEffect, useState } from "react";
import "./RecruiterDashBoard.css";
import JobPostCard from "../components/JobPostCard";
import Logout from "../components/auth/Logout"
import { FaPlus } from "react-icons/fa";
import axios from "axios";
import Select from "react-select";

const API_BASE = "http://127.0.0.1:8000";

const RecruiterDashBoard = () => {
  const [expandedJobId, setExpandedJobId] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [locations, setLocations] = useState([]);
  const [domains, setDomains] = useState([]);
  const [loadingPost, setLoadingPost] = useState(false);
  const [loadingJobs, setLoadingJobs] = useState(true);

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
      setLoadingJobs(true);
      const res = await axios.get(`${API_BASE}/jobs/postedjobs`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setJobs(res.data);
    } finally {
      setLoadingJobs(false);
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

  const handleSubmit = async () => {
    if (formData.location_ids.length === 0) {
      alert("Please select at least one location.");
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
      setLoadingPost(true);

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

      // Reset form
      setFormData({
        company_name: "",
        job_title: "",
        location_ids: [],
        industry_domain_id: "",
        min_experience: "",
        job_description: "",
      });

      fetchJobs();
      alert("Job successfully posted!");
    } catch (err) {
      alert("Failed to post job");
    } finally {
      setLoadingPost(false);
    }
  };

  const toggleDetails = (job_id) => {
    setExpandedJobId(expandedJobId === job_id ? null : job_id);
  };

  const deleteJob = async (job_id) => {
    await axios.delete(`${API_BASE}/jobs/${job_id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    setJobs((prev) => prev.filter((job) => job.job_id !== job_id));
  };

  const locationOptions = locations.map((loc) => ({
    value: loc.id,
    label: loc.name,
  }));

  return (
    <div className="page-container">
      <div className="top-bar">
        <Logout/>
      </div>
      <div className="workspace-container">
        <h1 className="workspace-title">Recruiter Workspace</h1>

        <div className="workspace-grid">
          <div className="post-job-card">
            <h2>
              <FaPlus className="icon-blue" /> Post a New Job
            </h2>

            <label>Company Name</label>
            <input
              type="text"
              name="company_name"
              value={formData.company_name}
              onChange={handleChange}
            />

            <label>Job Title</label>
            <input
              type="text"
              name="job_title"
              value={formData.job_title}
              onChange={handleChange}
            />

            <label>Locations</label>
            <Select
              options={locationOptions}
              isMulti
              placeholder="Search & select locations..."
              value={locationOptions.filter((option) =>
                formData.location_ids.includes(option.value)
              )}
              onChange={handleLocationChange}
            />

            <label>Industry Domain</label>
            <select
              name="industry_domain_id"
              value={formData.industry_domain_id}
              onChange={handleChange}
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

            <label>Minimum Required Experience (Years)</label>
            <select
              name="min_experience"
              value={formData.min_experience}
              onChange={handleChange}
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

            <label>Job Description</label>
            <textarea
              name="job_description"
              value={formData.job_description}
              onChange={handleChange}
            />

            <button
              className="publish-btn"
              onClick={handleSubmit}
              disabled={loadingPost}
            >
              {loadingPost ? "Posting..." : "Publish Job Posting"}
            </button>
          </div>

          <div className="jobs-section">
            <h2>Your Posted Jobs</h2>

            {loadingJobs ? (
              <p className="info-text">Loading your jobs...</p>
            ) : jobs.length === 0 ? (
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