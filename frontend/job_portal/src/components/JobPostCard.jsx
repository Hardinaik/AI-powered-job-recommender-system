
import { FaMapMarkerAlt, FaTrash } from "react-icons/fa";
import "./JobPostCard.css";

const JobPostCard = ({
  job,
  isExpanded,
  onToggle,
  onDelete
}) => {
  return (
    <div className={`job-card ${isExpanded ? "active" : ""}`}>
      <div className="job-top">
        <div>
          <h3>{job.title}</h3>
          <p className="job-meta">
            <FaMapMarkerAlt /> {job.location} • {job.type}
          </p>
        </div>

        <div className="job-actions">
          <button
            className="details-btn"
            onClick={() => onToggle(job.id)}
          >
            {isExpanded ? "Hide Details" : "View Details"}
          </button>

          <FaTrash
            className="delete-icon"
            onClick={() => onDelete(job.id)}
          />
        </div>
      </div>

      {isExpanded && job.requirements && (
        <div className="job-details">
          <div>
            <h4>Requirements</h4>
            <ul>
              {job.requirements.map((req, index) => (
                <li key={index}>{req}</li>
              ))}
            </ul>
          </div>

          <div>
            <h4>Summary</h4>
            <p>{job.summary}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobPostCard;
