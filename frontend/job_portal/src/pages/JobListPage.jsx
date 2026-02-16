import { useState } from "react";
import JobCard from "../components/jobCard";
import "./JobListPage.css";

function JobListPage() {
  // ------------------ Filter Options ------------------

  const domains = [
    "Technology / IT",
    "Software Development",
    "Artificial Intelligence & ML",
    "Data Science & Analytics"
  ];

  const locations = [
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
    "Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand",
    "Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur",
    "Meghalaya","Mizoram","Nagaland","Odisha","Punjab",
    "Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura",
    "Uttar Pradesh","Uttarakhand","West Bengal",
    "Andaman and Nicobar Islands","Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi","Jammu and Kashmir","Ladakh","Lakshadweep","Puducherry",
    "Remote"
  ];

  const experienceOptions = [
    ...Array.from({ length: 16 }, (_, i) => i),
    "15+"
  ];

  // ------------------ Job Data ------------------

  const allJobs = [
    {
      id: 1,
      title: "Frontend Developer",
      company: "TechFlow Systems",
      location: "Gujarat",
      domain: "Technology / IT",
      experience: 2,
      salary: "₹6L - ₹10L",
      type: "Full-time",
      match: 82,
      description:
        "Looking for a React developer with experience in modern UI frameworks and REST API integration."
    },
    {
      id: 2,
      title: "Data Scientist",
      company: "Neon Health",
      location: "Karnataka",
      domain: "Data Science & Analytics",
      experience: 5,
      salary: "₹12L - ₹18L",
      type: "Full-time",
      match: 91,
      description:
        "Seeking a Data Scientist skilled in Python, ML models, and data visualization tools."
    }
  ];

  // ------------------ States ------------------

  const [jobs, setJobs] = useState(allJobs);
  const [domain, setDomain] = useState("");
  const [location, setLocation] = useState("");
  const [experience, setExperience] = useState("");

  // ------------------ Filter Logic ------------------

  const applyFilters = () => {
    const filtered = allJobs.filter((job) => {
      const domainMatch = domain ? job.domain === domain : true;
      const locationMatch = location ? job.location === location : true;

      let experienceMatch = true;

      if (experience === "15+") {
        experienceMatch = job.experience >= 15;
      } else if (experience !== "") {
        experienceMatch = job.experience <= Number(experience);
      }

      return domainMatch && locationMatch && experienceMatch;
    });

    setJobs(filtered);
  };

  const resetFilters = () => {
    setDomain("");
    setLocation("");
    setExperience("");
    setJobs(allJobs);
  };

  // ------------------ JSX ------------------

  return (
    <div className="job-page">
      {/* Sidebar */}
      <aside className="filters">
        <h3 className="filters-title">Filters</h3>
        <p className="filters-subtitle">
          Refine jobs based on your preferences
        </p>

        {/* Industry Domain */}
        <div className="filter-group">
          <label>Industry Domain</label>
          <select value={domain} onChange={(e) => setDomain(e.target.value)}>
            <option value="">Select</option>
            {domains.map((item, index) => (
              <option key={index} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>

        {/* Location */}
        <div className="filter-group">
          <label>Location</label>
          <select value={location} onChange={(e) => setLocation(e.target.value)}>
            <option value="">Select</option>
            {locations.map((item, index) => (
              <option key={index} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>

        {/* Experience */}
        <div className="filter-group">
          <label>Experience (Years)</label>
          <select
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
          >
            <option value="">Select</option>
            {experienceOptions.map((exp, index) => (
              <option key={index} value={exp}>
                {exp === "15+" ? "15+ Years" : `${exp} Years`}
              </option>
            ))}
          </select>
        </div>

        {/* Resume Upload (UI only for now) */}
        <div className="upload-box">
          <button className="browse-btn">Browse</button>
          <p>Drop a file here</p>
          <small>*PDF file supported</small>
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
