import React, { useEffect, useState } from "react";
import "./RecruiterDashBoard.css";
import JobPostCard from "../components/JobPostCard";
import { FaPlus } from "react-icons/fa";
import axios from "axios";

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
    location_id: "",
    industry_domain_id: "",
    min_experience: "",
    max_experience: "",
    job_description: "",
  });

  const token = localStorage.getItem("token");

  //Fetch Locations
  const fetchLocations = async () => {
    const res = await axios.get(`${API_BASE}/jobs/locations`);
    setLocations(res.data);
  };

  //Fetch Industry Domains
  const fetchDomains = async () => {
    const res = await axios.get(`${API_BASE}/jobs/industry-domains`);
    setDomains(res.data);
  };

  //Fetch Posted Jobs
  const fetchJobs = async () => {
    try {
      setLoadingJobs(true);

      const res = await axios.get(`${API_BASE}/jobs/postedjobs`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setJobs(res.data);
    } catch (error) {
      console.error("Error fetching jobs", error);
    } finally {
      setLoadingJobs(false);
    }
  };

  useEffect(() => {
    fetchLocations();
    fetchDomains();
    fetchJobs();
  }, []);

  //Handle Form Change
  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  //Submit Job
  const handleSubmit = async () => {
    try {
      setLoadingPost(true);

      const payload = {
        ...formData,
        location_id: Number(formData.location_id),
        industry_domain_id: Number(formData.industry_domain_id),
        min_experience: Number(formData.min_experience),
        max_experience: Number(formData.max_experience),
      };

      await axios.post(`${API_BASE}/jobs/post`, payload, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      // Reset form
      setFormData({
        company_name: "",
        job_title: "",
        location_id: "",
        industry_domain_id: "",
        min_experience: "",
        max_experience: "",
        job_description: "",
      });

      await fetchJobs();

      alert("Job successfully posted!");

    } catch (error) {
      console.error("Error posting job", error);
      alert("Failed to post job");
    } finally {
      setLoadingPost(false);
    }
  };

  // Toggle Details
  const toggleDetails = (job_id) => {
    setExpandedJobId(expandedJobId === job_id ? null : job_id);
  };

  //Delete Job
  const deleteJob = async (job_id) => {
    try {
      await axios.delete(`${API_BASE}/jobs/${job_id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setJobs((prevJobs) =>
        prevJobs.filter((job) => job.job_id !== job_id)
      );

    } catch (error) {
      console.error("Error deleting job", error);
      alert("Error deleting job");
    }
  };

  return (
    <div className="workspace-container">
      <h1 className="workspace-title">Recruiter Workspace</h1>

      <div className="workspace-grid">
        {/* post job from*/}
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

          <label>Location</label>
          <select
            name="location_id"
            value={formData.location_id}
            onChange={handleChange}
          >
            <option value="">Select Location</option>
            {locations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name}
              </option>
            ))}
          </select>

          <label>Industry Domain</label>
          <select
            name="industry_domain_id"
            value={formData.industry_domain_id}
            onChange={handleChange}
          >
            <option value="">Select Domain</option>
            {domains.map((domain) => (
              <option key={domain.id} value={domain.id}>
                {domain.name}
              </option>
            ))}
          </select>

          <label>Experience Range</label>
          <div className="row">
            <input
              type="number"
              name="min_experience"
              value={formData.min_experience}
              onChange={handleChange}
              placeholder="Min"
            />
            <input
              type="number"
              name="max_experience"
              value={formData.max_experience}
              onChange={handleChange}
              placeholder="Max"
            />
          </div>

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
            {loadingPost ? "Posting Job..." : "Publish Job Posting"}
          </button>
        </div>

        {/* posted job list*/}
        <div className="jobs-section">
          <h2>Your Posted Jobs</h2>

          {loadingJobs ? (
            <p className="info-text">Loading your jobs...</p>
          ) : jobs.length === 0 ? (
            <p className="info-text">
              You haven’t posted any jobs yet.
              <br />
              Start by creating your first job posting!
            </p>
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
  );
};

export default RecruiterDashBoard;