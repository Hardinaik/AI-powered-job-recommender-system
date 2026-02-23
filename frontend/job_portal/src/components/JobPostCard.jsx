import { FaMapMarkerAlt, FaTrash } from "react-icons/fa";
import "./JobPostCard.css";

const JobPostCard = ({ job, isExpanded, onToggle, onDelete }) => {
  return (
    <div className={`job-card ${isExpanded ? "active" : ""}`}>
      
      {/* header*/}
      <div className="job-header">
        <div>
          <h3 className="job-title">{job.job_title}</h3>
          <p className="job-location">
            <FaMapMarkerAlt /> {job.location}
          </p>
        </div>

        <div className="job-actions">
          <button
            className="details-btn"
            onClick={() => onToggle(job.job_id)}
          >
            {isExpanded ? "Hide Details" : "View Details"}
          </button>

          <FaTrash
            className="delete-icon"
            onClick={() => onDelete(job.job_id)}
          />
        </div>
      </div>

      {/* description details */}
      {isExpanded && (
        <>
          <hr className="divider" />
          <div className="job-description">
            {job.job_description}
          </div>
        </>
      )}
    </div>
  );
};

export default JobPostCard;