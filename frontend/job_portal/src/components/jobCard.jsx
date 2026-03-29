import { useState, useEffect } from "react";
import { FaBookmark } from "react-icons/fa";
import api from "../api/axios";
import "./jobCard.css";
 
function JobCard({ job, isSaved, isApplied, onStatusChange }) {
  const [showDetails, setShowDetails] = useState(false);
  const [saved, setSaved] = useState(isSaved);
  const [applied, setApplied] = useState(isApplied);
 
  useEffect(() => { setSaved(isSaved); }, [isSaved]);
  useEffect(() => { setApplied(isApplied); }, [isApplied]);
 
  const handleSaveJob = async () => {
    if (saved) return;
    try {
      await api.post(`/applications/jobs/${job.job_id}/save`);
      setSaved(true);
      if (onStatusChange) onStatusChange(job.job_id, "save");
    } catch (error) {
      if (error.response?.status === 409) {
        setSaved(true);
        if (onStatusChange) onStatusChange(job.job_id, "save");
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
      if (onStatusChange) onStatusChange(job.job_id, "apply");
    } catch (error) {
      if (error.response?.status === 409) {
        setApplied(true);
        if (onStatusChange) onStatusChange(job.job_id, "apply");
      } else {
        alert(error.response?.data?.detail || "Failed to apply");
      }
    }
  };
 
  return (
    <div className="job-card">
 
      {/* Match Badge */}
      {job.match_score > 0 && (
        <div className="match-badge">{Math.round(job.match_score)}% Match</div>
      )}
 
      {/* Header */}
      <div className="job-card-header">
        <div className="job-title">
          <h3>{job.job_title}</h3>
          <p className="company">
            {job.company_name}
            {job.locations?.length > 0 && <> &bull; {job.locations.join(", ")}</>}
            {job.min_experience != null && <> &bull; {job.min_experience} yr{job.min_experience !== 1 ? "s" : ""} exp</>}
          </p>
        </div>
      </div>
 
      <div className="job-card-divider" />
 
      {/* Description */}
      <div className="job-description">
        <div className="jd-header">
          <span className="jd-label">Job Description</span>
          <button className="details-btn" onClick={() => setShowDetails(!showDetails)}>
            {showDetails ? "Hide Details" : "View Details"}
          </button>
        </div>
        <p className={showDetails ? "" : "jd-preview"}>{job.job_description}</p>
      </div>
 
      {/* Footer */}
      <div className="job-card-footer">
        <button
          className={`apply-btn ${applied ? "applied" : ""}`}
          onClick={handleApplyJob}
          disabled={applied}
        >
          {applied ? " Applied" : "Apply Now"}
        </button>
 
        <button
          className={`save-btn ${saved ? "saved" : ""}`}
          onClick={handleSaveJob}
          disabled={saved}
          aria-label={saved ? "Job saved" : "Save job"}
          title={saved ? "Saved" : "Save job"}
        >
          <FaBookmark />
        </button>
      </div>
 
    </div>
  );
}
 
export default JobCard;