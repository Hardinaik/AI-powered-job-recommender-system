import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import JobCard from "../components/jobCard";
import Logout from "../components/auth/Logout";
import Loader from "../components/loader";
import api from "../api/axios";
import "./JobListPage.css";
 
function JobListPage() {
  const navigate = useNavigate();
  const [domains, setDomains] = useState([]);
  const [locations, setLocations] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [savedJobIds, setSavedJobIds] = useState([]);
  const [appliedJobIds, setAppliedJobIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [useSavedResume, setUseSavedResume] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [view, setView] = useState("all");
  const [domainId, setDomainId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [experience, setExperience] = useState("");
 
  const experienceOptions = [...Array.from({ length: 31 }, (_, i) => i)];
 
  // 1. Initial Load: IDs and Form Options
  useEffect(() => {
    const initData = async () => {
      setLoading(true);
      try {
        const [domainRes, locationRes, savedIdsRes, appliedIdsRes] = await Promise.all([
          api.get("/jobs/industry-domains"),
          api.get("/jobs/locations"),
          api.get("/applications/saved-jobs/ids"),
          api.get("/applications/applied-jobs/ids"),
        ]);
 
        setDomains(domainRes.data);
        setLocations(locationRes.data);
        setSavedJobIds(savedIdsRes.data);
        setAppliedJobIds(appliedIdsRes.data);
 
        await applyFilters();
      } catch (error) {
        console.error("Initialization failed", error);
      } finally {
        setLoading(false);
      }
    };
    initData();
  }, []);
 
  // 2. Fetch Detailed Content when View Changes
  useEffect(() => {
    const fetchViewData = async () => {
      if (view === "all") {
        applyFilters();
        return;
      }
 
      setLoading(true);
      try {
        const endpoint =
          view === "saved"
            ? "/applications/saved-jobs/details"
            : "/applications/applied-jobs/details";
 
        const res = await api.get(endpoint);
        setJobs(res.data);
      } catch (error) {
        console.error("Failed to fetch view details", error);
        setJobs([]);
      } finally {
        setLoading(false);
      }
    };
 
    fetchViewData();
  }, [view]);
 
  const handleStatusChange = (jobId, type) => {
    if (type === "save") {
      setSavedJobIds((prev) => [...new Set([...prev, jobId])]);
    } else if (type === "apply") {
      setAppliedJobIds((prev) => [...new Set([...prev, jobId])]);
    }
  };
 
  const applyFilters = async () => {
    setLoading(true);
    try {
      const params = {};
      if (domainId) params.domain_id = domainId;
      if (locationId) params.location_id = locationId;
      if (experience !== "") params.experience = experience;
 
      const formData = new FormData();
      formData.append("use_saved_resume", useSavedResume);
      if (selectedFile) formData.append("resume_file", selectedFile);
 
      const response = await api.post("/recommendations/jobs", formData, { params });
      setJobs(response.data);
    } catch (error) {
      console.error("Fetch failed", error);
    } finally {
      setLoading(false);
    }
  };
 
  const resetFilters = () => {
    setDomainId("");
    setLocationId("");
    setExperience("");
    setUseSavedResume(false);
    setSelectedFile(null);
    fetchJobsWithEmptyFilters();
  };
 
  const fetchJobsWithEmptyFilters = async () => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("use_saved_resume", false);
      const response = await api.post("/recommendations/jobs", formData, { params: {} });
      setJobs(response.data);
      setView("all");
    } catch (error) {
      console.error("Reset fetch failed", error);
    } finally {
      setLoading(false);
    }
  };
 
  const viewLabel =
    view === "all" ? "Job Listings" : view === "saved" ? "Saved Jobs" : "Applied Jobs";
 
  return (
    <div className="page-container">
 
      {/* ── Top Bar ── */}
      <div className="top-bar">
        <button
          className={`top-btn ${view === "all" ? "active" : ""}`}
          onClick={() => setView("all")}
        >
          All Jobs
        </button>
        <button
          className={`top-btn ${view === "saved" ? "active" : ""}`}
          onClick={() => setView("saved")}
        >
          Saved Jobs
        </button>
        <button
          className={`top-btn ${view === "applied" ? "active" : ""}`}
          onClick={() => setView("applied")}
        >
          Applied Jobs
        </button>
        <button className="profile-btn" onClick={() => navigate("/profile")}>
          Profile
        </button>
        <Logout />
      </div>
 
      {/* ── Body ── */}
      <div className="job-page">
 
        {/* ── Filters Sidebar ── */}
        <aside className="filters">
          <h3 className="filters-title">Filters</h3>
          <div className="filter-divider" />
 
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
                <option key={exp} value={exp}>
                  {exp === 0 ? "Fresher (0 years)" : `${exp} year${exp > 1 ? "s" : ""}`}
                </option>
              ))}
            </select>
          </div>
 
          <div className="filter-group">
            <label>Resume Recommendation</label>
            <div className="old-resume-checkbox">
              <input
                type="checkbox"
                id="useOldResume"
                checked={useSavedResume}
                onChange={(e) => setUseSavedResume(e.target.checked)}
              />
              <label htmlFor="useOldResume">Use saved resume</label>
            </div>
            <div className={`upload-box ${useSavedResume ? "disabled-upload" : ""}`}>
              <input
                type="file"
                id="resume-file"
                accept=".pdf"
                onChange={(e) => setSelectedFile(e.target.files[0])}
                disabled={useSavedResume}
                hidden
              />
              <button
                className="browse-btn"
                disabled={useSavedResume}
                onClick={() => document.getElementById("resume-file").click()}
              >
                Browse Files
              </button>
              <p>{selectedFile ? selectedFile.name : "PDF, max 5 MB"}</p>
            </div>
          </div>
 
          <div className="filter-actions">
            <button className="apply-btn" onClick={applyFilters} disabled={loading}>
              {loading ? "Searching…" : "Apply Filters"}
            </button>
            <button className="reset-btn" onClick={resetFilters}>
              Reset All
            </button>
          </div>
        </aside>
 
        {/* ── Job List ── */}
        <main className="job-list">
          <div className="job-list-header">
            <h3 className="job-list-title">{viewLabel}</h3>
            {!loading && (
              <span className="job-list-badge">{jobs.length} listing{jobs.length !== 1 ? "s" : ""}</span>
            )}
          </div>
 
          {loading ? (
            <Loader />
          ) : jobs.length === 0 ? (
            <div className="empty-state">No jobs found</div>
          ) : (
            <div className="job-list-items">
              {jobs.map((job) => (
                <JobCard
                  key={job.job_id}
                  job={job}
                  isSaved={savedJobIds.includes(job.job_id)}
                  isApplied={appliedJobIds.includes(job.job_id)}
                  onStatusChange={handleStatusChange}
                />
              ))}
            </div>
          )}
        </main>
 
      </div>
    </div>
  );
}
 
export default JobListPage;