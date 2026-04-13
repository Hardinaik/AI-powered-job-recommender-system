import { useState, useEffect } from "react";
import { FaBookmark, FaBuilding } from "react-icons/fa";
import api from "../api/axios";
import CompanyCard from "./CompanyCard";
import ApplyModal from "./ApplyModal";       
import "./jobCard.css";

function JobCard({ job, isSaved, isApplied, onStatusChange }) {
  const [showDetails, setShowDetails] = useState(false);
  const [saved, setSaved] = useState(isSaved);
  const [applied, setApplied] = useState(isApplied);
  const [showCompany, setShowCompany] = useState(false);
  const [showApplyModal, setShowApplyModal] = useState(false);  

  useEffect(() => { setSaved(isSaved); }, [isSaved]);
  useEffect(() => { setApplied(isApplied); }, [isApplied]);

  const handleSaveToggle = async () => {
    if (saved) {
      try {
        await api.delete(`/applications/jobs/${job.job_id}/unsave`);
        setSaved(false);
        if (onStatusChange) onStatusChange(job.job_id, "unsave");
      } catch (error) {
        if (error.response?.status === 404) {
          setSaved(false);
          if (onStatusChange) onStatusChange(job.job_id, "unsave");
        } else {
          alert(error.response?.data?.detail || "Failed to unsave job");
        }
      }
    } else {
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
    }
  };

  // Opens the modal instead of directly calling the API
  const handleApplyClick = () => {
    if (applied) return;
    setShowApplyModal(true);
  };

  // Called by ApplyModal after successful submission
  const handleApplied = (jobId) => {
    setApplied(true);
    setShowApplyModal(false);
    if (onStatusChange) onStatusChange(jobId, "apply");
  };

  return (
    <>
      <div className="job-card">

        {/* Match Badge */}
        {job.match_score >= 0 && (
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
            onClick={handleApplyClick}
            disabled={applied}
          >
            {applied ? "Applied" : "Apply Now"}
          </button>

          <button
            className="company-btn"
            onClick={() => setShowCompany(true)}
            title="View company details"
          >
            <FaBuilding className="company-btn-icon" />
            Company Info
          </button>

          <button
            className={`save-btn ${saved ? "saved" : ""}`}
            onClick={handleSaveToggle}
            aria-label={saved ? "Unsave job" : "Save job"}
            title={saved ? "Unsave job" : "Save job"}
          >
            <FaBookmark />
          </button>
        </div>

      </div>

      {/* Apply Modal */}
      {showApplyModal && (
        <ApplyModal
          job={job}
          onClose={() => setShowApplyModal(false)}
          onApplied={handleApplied}
        />
      )}

      {/* Company Details Modal */}
      {showCompany && (
        <CompanyCard
          jobId={job.job_id}
          companyName={job.company_name}
          onClose={() => setShowCompany(false)}
        />
      )}
    </>
  );
}

export default JobCard;