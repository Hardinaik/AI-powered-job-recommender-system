import "./jobCard.css";
import { FaBookmark } from "react-icons/fa";

function JobCard({ job }) {
  return (
    <div className="job-card">
      <div className="job-card-header">
        <div className="job-title">
          <span className="job-icon"></span>
          <div>
            <h3>{job.title}</h3>
            <p className="company">
              {job.company} • {job.location}
            </p>
          </div>
        </div>

        <div className="match-score">
          <span>{job.match}%</span>
          <small>Match</small>
        </div>
      </div>

      <div className="job-description">
        <strong>JOB DESCRIPTION</strong>
        <p>{job.description}</p>
      </div>

      {/* Footer */}
      <div className="job-card-footer">
        <button className="apply-btn">Apply Now</button>

        <button className="save-btn">
          <FaBookmark />
        </button>
      </div>
    </div>
  );
}

export default JobCard;
