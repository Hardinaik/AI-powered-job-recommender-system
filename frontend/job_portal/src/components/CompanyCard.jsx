import { useState, useEffect, useCallback } from "react";
import { FaTimes, FaGlobe, FaLinkedin, FaBuilding } from "react-icons/fa";
import api from "../api/axios";
import "./CompanyCard.css";

function CompanyCard({ jobId, companyName, onClose }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.get(`/applications/jobs/${jobId}/company-details`);
        setDetails(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load company details");
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [jobId]);

  // Close on backdrop click
  const handleBackdropClick = useCallback((e) => {
    if (e.target === e.currentTarget) onClose();
  }, [onClose]);

  // Close on Escape key
  useEffect(() => {
    const handleKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  // Derive initials from company name for avatar
  const initials = (companyName || "Co")
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");

  return (
    <div className="company-overlay" onClick={handleBackdropClick}>
      <div className="company-modal" role="dialog" aria-modal="true" aria-label="Company details">

        {/* Modal Header */}
        <div className="company-modal-header">
          <div className="company-avatar">{initials}</div>
          <div className="company-modal-title">
            <h2>{details?.company_name || companyName || "Company"}</h2>
            <span className="company-modal-subtitle">Company Profile</span>
          </div>
          <button className="company-close-btn" onClick={onClose} aria-label="Close">
            <FaTimes />
          </button>
        </div>

        <div className="company-modal-divider" />

        {/* Modal Body */}
        <div className="company-modal-body">

          {loading && (
            <div className="company-state company-loading">
              <div className="company-spinner" />
              <p>Loading company details…</p>
            </div>
          )}

          {!loading && error && (
            <div className="company-state company-error">
              <FaBuilding className="company-state-icon" />
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && details && (
            <>
              {/* Description */}
              {details.description && (
                <div className="company-section">
                  <span className="company-section-label">About</span>
                  <p className="company-section-text">{details.description}</p>
                </div>
              )}

              {/* Links */}
              {(details.website || details.linkedin) && (
                <div className="company-section">
                  <span className="company-section-label">Links</span>
                  <div className="company-links">
                    {details.website && (
                      <a
                        href={details.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="company-link"
                      >
                        <FaGlobe className="company-link-icon" />
                        Website
                      </a>
                    )}
                    {details.linkedin && (
                      <a
                        href={details.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="company-link company-link--linkedin"
                      >
                        <FaLinkedin className="company-link-icon" />
                        LinkedIn
                      </a>
                    )}
                  </div>
                </div>
              )}

              {/* Fallback if no details at all */}
              {!details.description && !details.website && !details.linkedin && (
                <div className="company-state company-empty">
                  <FaBuilding className="company-state-icon" />
                  <p>No additional company details available.</p>
                </div>
              )}
            </>
          )}

        </div>
      </div>
    </div>
  );
}

export default CompanyCard;