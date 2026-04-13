import { FaMapMarkerAlt, FaTrash } from "react-icons/fa";
import "./JobPostCard.css";

const JobPostCard = ({ job, isExpanded, onToggle, onDelete }) => {
  return (
    <div className={`jpc-card ${isExpanded ? "jpc-card--active" : ""}`}>

      <div className="jpc-header">
        <div className="jpc-meta">
          <h3 className="jpc-title">{job.job_title}</h3>
          <div className="jpc-tags">

              <span className="jpc-badge jpc-badge--id">
                #{job.job_id.toString()}
              </span>

            {job.locations && job.locations.length > 0 ? (
              job.locations.map((loc, i) => (
                <span key={i} className="jpc-badge jpc-badge--location">
                  <FaMapMarkerAlt style={{ fontSize: 10 }} /> {loc}
                </span>
              ))
            ) : (
              <span className="jpc-badge jpc-badge--muted"></span>
            )}
            {job.min_experience != null && (
              <span className="jpc-badge jpc-badge--exp">
                {job.min_experience === 0 ? "Fresher" : `${job.min_experience} yrs`}
              </span>
            )}
          </div>
        </div>

        <div className="jpc-actions">
          <button
            className={`jpc-details-btn ${isExpanded ? "jpc-details-btn--active" : ""}`}
            onClick={() => onToggle(job.job_id)}
          >
            {isExpanded ? "Hide Details" : "View Details"}
          </button>
          <button
            className="jpc-delete-btn"
            onClick={() => onDelete(job.job_id)}
            title="Delete job"
          >
            <FaTrash style={{ fontSize: 12 }} />
          </button>
        </div>
      </div>

      {isExpanded && (
        <>
          <div className="jpc-divider" />
          <p className="jpc-description">{job.job_description}</p>
        </>
      )}
    </div>
  );
};

export default JobPostCard;