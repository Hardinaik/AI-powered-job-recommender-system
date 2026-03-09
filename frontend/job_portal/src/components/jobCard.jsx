import { useState, useEffect } from "react";
import { FaBookmark } from "react-icons/fa";
import api from "../api/axios";
import "./jobCard.css";

function JobCard({ job, isSaved, isApplied }) {
  const [showDetails, setShowDetails] = useState(false);
  const [saved, setSaved] = useState(isSaved);
  const [applied, setApplied] = useState(isApplied);

  useEffect(() => {
    setSaved(isSaved);
  }, [isSaved]);

  useEffect(() => {
    setApplied(isApplied);
  }, [isApplied]);

  const handleSaveJob = async () => {
    if (saved) return;

    try {
      await api.post(`/applications/jobs/${job.job_id}/save`);
      setSaved(true);
    } catch (error) {
      if (error.response?.status === 409) {
        setSaved(true);
      } else {
        alert(error.response?.data?.detail || "Failed to save job");
      }
    }
  };

  const handleApplyJob = async () => {
    if (applied) return;

    try {
      await api.post(`/applications/job/${job.job_id}/apply`);
      setApplied(true);
    } catch (error) {
      if (error.response?.status === 409) {
        setApplied(true);
      } else {
        alert(error.response?.data?.detail || "Failed to apply");
      }
    }
  };

  return (
    <div className="job-card">
      <div className="job-card-header">
        <div className="job-title">
          <div>
            <h3>{job.job_title}</h3>
            <p className="company">
              {job.company_name} • {job.locations?.join(", ")} • {job.min_experience} yrs exp
            </p>
          </div>
        </div>
      </div>

      <div className="job-description">
        <div className="jd-header">
          <strong>JOB DESCRIPTION</strong>
          <button
            className="details-btn"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? "Hide Details" : "View Details"}
          </button>
        </div>
        <p className={showDetails ? "" : "jd-preview"}>
          {job.job_description}
        </p>
      </div>

      <div className="job-card-footer">
        <button
          className={`apply-btn ${applied ? "applied" : ""}`}
          onClick={handleApplyJob}
          disabled={applied}
        >
          {applied ? "Applied" : "Apply Now"}
        </button>

        <button
          className={`save-btn ${saved ? "saved" : ""}`}
          onClick={handleSaveJob}
          disabled={saved}
          aria-label="Save Job"
        >
          <FaBookmark />
        </button>
      </div>
    </div>
  );
}

export default JobCard;