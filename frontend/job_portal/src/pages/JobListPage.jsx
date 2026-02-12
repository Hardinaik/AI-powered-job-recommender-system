import { useState } from "react";
import JobCard from "../components/jobCard";
import "./JobListPage.css";

function JobListPage() {
  const allJobs = [
    {
      id: 1,
      title: "Senior Product Designer",
      company: "TechFlow Systems",
      location: "San Francisco",
      match: 98,
      description: "Senior designer role...",
      type: "Full-time",
      salary: "$140k - $180k",
      domain: "Design",
    },
    {
      id: 2,
      title: "Lead UX Architect",
      company: "Neon Health",
      location: "Austin",
      match: 92,
      description: "UX architect role...",
      type: "Remote",
      salary: "$160k - $210k",
      domain: "Technology",
    },
  ];

  const [jobs, setJobs] = useState(allJobs);
  const [location, setLocation] = useState("");
  const [domain, setDomain] = useState("");
  const [hasFiltered, setHasFiltered] = useState(false);

  const applyFilters = () => {
    const results = allJobs.filter((job) => {
      return (
        (location ? job.location.includes(location) : true) &&
        (domain ? job.domain === domain : true)
      );
    });

    setJobs(results);
    setHasFiltered(true);
  };

  const resetFilters = () => {
    setLocation("");
    setDomain("");
    setJobs(allJobs);
    setHasFiltered(false);
  };

  return (
    <div className="job-page">
      {/* Sidebar */}
      <aside className="filters">
        <h3 className="filters-title">Filters</h3>
        <p className="filters-subtitle">
          Refine jobs based on your preferences
        </p>

        <div className="upload-box">
          <button className="browse-btn">Browse</button>
          <p>drop a file here</p>
          <small>*PDF file supported</small>
        </div>

        <div className="filter-group">
          <label>Location</label>
          <select
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          >
            <option value="">Select</option>
            <option value="San Francisco">San Francisco</option>
            <option value="Austin">Austin</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Industry Domain</label>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
          >
            <option value="">Select</option>
            <option value="Design">Design</option>
            <option value="Technology">Technology</option>
          </select>
        </div>

        <div className="filter-actions">
          <button className="apply-btn" onClick={applyFilters}>
            Apply Filters
          </button>

          <button className="reset-btn" onClick={resetFilters}>
            Reset All Filters
          </button>
        </div>
      </aside>

      {/* Job List */}
      <main className="job-list">
        <h3>Job Listings</h3>
        <p className="subtitle">
          Based on your current filters and profile preferences.
        </p>

        {jobs.length === 0 && (
          <div className="empty-state">
            No jobs found for selected filters
          </div>
        )}

        {jobs.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </main>
    </div>
  );
}

export default JobListPage;
