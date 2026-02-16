import React, { useState } from "react";
import "./RecruiterDashBoard.css";
import JobPostCard from "../components/JobPostCard";
import { FaPlus, FaFilter } from "react-icons/fa";

const RecruiterDashBoard = () => {
  const [expandedJobId, setExpandedJobId] = useState(null);

  const [jobs, setJobs] = useState([
    {
      id: "8821",
      title: "NLP Research Scientist",
      location: "Palo Alto, CA",
      type: "Full-time",
    },
    {
      id: "9402",
      title: "Computer Vision Lead",
      location: "Austin, TX",
      type: "Remote",
    },
    {
      id: "1022",
      title: "AI Product Manager",
      location: "New York, NY",
      type: "On-site",
    },
    {
      id: "2245",
      title: "Backend Infrastructure (AI Core)",
      location: "Seattle, WA",
      type: "Full-time",
      requirements: [
        "5-8 years of experience",
        "Strong Go/Rust fundamentals",
        "Distributed systems knowledge",
      ],
      summary:
        "Leading the architectural development of our core inference engine. Working closely with researchers to optimize model deployments.",
    },
  ]);

  const toggleDetails = (id) => {
    setExpandedJobId(expandedJobId === id ? null : id);
  };

  const deleteJob = (id) => {
    setJobs(jobs.filter((job) => job.id !== id));
  };

  return (
    <div className="workspace-container">
      <h1 className="workspace-title">Recruiter Workspace</h1>
      <p className="workspace-subtitle">
        Manage your active positions and source top-tier talent.
      </p>

      <div className="workspace-grid">
        {/* left side */}
        <div className="post-job-card">
          <h2>
            <FaPlus className="icon-blue" /> Post a New Job
          </h2>

          <label>Company Name</label>
          <input type="text" placeholder="e.g. Nexus AI Labs" />

          <label>Job Role / Title</label>
          <input type="text" placeholder="e.g. Senior ML Engineer" />

          <label>Location</label>
          <input type="text" placeholder="San Francisco, CA" />

          <label>Experience Range (Years)</label>
          <div className="row">
            <input type="number" placeholder="Min" />
            <input type="number" placeholder="Max" />
          </div>

          <label>Job Description</label>
          <textarea placeholder="Outline responsibilities, skills, and benefits..." />

          <button className="publish-btn">Publish Job Posting</button>
        </div>

        {/* right side */}
        <div className="jobs-section">
          <div className="jobs-header">
            <h2>Your Posted Jobs</h2>
            <button className="filter-btn">
              <FaFilter />
            </button>
          </div>

          {jobs.map((job) => (
            <JobPostCard
              key={job.id}
              job={job}
              isExpanded={expandedJobId === job.id}
              onToggle={toggleDetails}
              onDelete={deleteJob}
            />
          ))}

          <button className="load-more">Load 10 more results</button>
        </div>
      </div>
    </div>
  );
};

export default RecruiterDashBoard;
