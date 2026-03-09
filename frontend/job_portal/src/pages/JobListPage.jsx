import { useState, useEffect } from "react";
import JobCard from "../components/jobCard";
import Logout from "../components/auth/Logout";
import api from "../api/axios";
import "./JobListPage.css";

function JobListPage() {
  const [domains, setDomains] = useState([]);
  const [locations, setLocations] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [savedJobIds, setSavedJobIds] = useState([]);
  const [appliedJobIds, setAppliedJobIds] = useState([]);
  const [loading, setLoading] = useState(false);

  // Filter States (Storing IDs)
  const [domainId, setDomainId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [experience, setExperience] = useState("");

  const experienceOptions = [...Array.from({ length: 31 }, (_, i) => i)];

  useEffect(() => {
    const initData = async () => {
      try {
        const [domainRes, locationRes, jobsRes, savedRes, appliedRes] = await Promise.all([
          api.get("/jobs/industry-domains"),
          api.get("/jobs/locations"),
          api.get("/recommendations/jobs"),
          api.get("/applications/saved-jobs"),
          api.get("/applications/applied-jobs"),
        ]);

        setDomains(domainRes.data);
        setLocations(locationRes.data);
        setJobs(jobsRes.data);
        setSavedJobIds(savedRes.data);
        setAppliedJobIds(appliedRes.data);
      } catch (error) {
        console.error("Initialization failed", error);
      }
    };
    initData();
  }, []);

  const applyFilters = async () => {
    setLoading(true);
    try {
      const response = await api.get("/recommendations/jobs", {
        params: {
          domain_id: domainId || undefined,
          location_id: locationId || undefined,
          experience: experience || undefined,
        },
      });
      setJobs(response.data);
    } catch (error) {
      console.error("Filtering failed", error);
    } finally {
      setLoading(false);
    }
  };

  const resetFilters = async () => {
    setDomainId("");
    setLocationId("");
    setExperience("");
    setLoading(true);
    try {
      const res = await api.get("/recommendations/jobs");
      setJobs(res.data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="top-bar"><Logout /></div>
      <div className="job-page">
        <aside className="filters">
          <h3 className="filters-title">Filters</h3>

          <div className="filter-group">
            <label>Industry Domain</label>
            <select value={domainId} onChange={(e) => setDomainId(e.target.value)}>
              <option value="">All Domains</option>
              {domains.map((item) => (
                <option key={item.id} value={item.id}>{item.name}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Location</label>
            <select value={locationId} onChange={(e) => setLocationId(e.target.value)}>
              <option value="">All Locations</option>
              {locations.map((item) => (
                <option key={item.id} value={item.id}>{item.name}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Experience (Years)</label>
            <select value={experience} onChange={(e) => setExperience(e.target.value)}>
              <option value="">Any Experience</option>
              {experienceOptions.map((exp) => (
                <option key={exp} value={exp}>{exp} Years</option>
              ))}
            </select>
          </div>

          <div className="filter-actions">
            <button className="apply-btn" onClick={applyFilters} disabled={loading}>
              {loading ? "Searching..." : "Apply Filters"}
            </button>
            <button className="reset-btn" onClick={resetFilters}>Reset All</button>
          </div>
        </aside>

        <main className="job-list">
          <h3>Job Listings</h3>
          {jobs.length === 0 ? (
            <div className="empty-state">No jobs found</div>
          ) : (
            jobs.map((job) => (
              <JobCard
                key={job.job_id}
                job={job}
                isSaved={savedJobIds.includes(job.job_id)}
                isApplied={appliedJobIds.includes(job.job_id)}
              />
            ))
          )}
        </main>
      </div>
    </div>
  );
}

export default JobListPage;