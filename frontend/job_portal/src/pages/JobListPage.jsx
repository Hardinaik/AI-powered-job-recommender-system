import { useState, useEffect } from "react";
import JobCard from "../components/jobCard";
import Logout from "../components/auth/Logout";
import Loader from "../components/loader";
import api from "../api/axios";
import "./JobListPage.css";

function JobListPage() {
  const [domains, setDomains] = useState([]);
  const [locations, setLocations] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [savedJobIds, setSavedJobIds] = useState([]);
  const [appliedJobIds, setAppliedJobIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [useSavedResume, setUseSavedResume] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  // Filter States
  const [domainId, setDomainId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [experience, setExperience] = useState("");

  const experienceOptions = [...Array.from({ length: 31 }, (_, i) => i)];

  useEffect(() => {
    const initData = async () => {
      setLoading(true);
      try {
        // We use an empty FormData for the initial POST call to match backend expectations
        const initialFormData = new FormData();

        const [domainRes, locationRes, jobsRes, savedRes, appliedRes] = await Promise.all([
          api.get("/jobs/industry-domains"),
          api.get("/jobs/locations"),
          api.post("/recommendations/jobs", initialFormData), 
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
      } finally {
        setLoading(false);
      }
    };
    initData();
  }, []);

  const handleCheckboxChange = (e) => {
    const isChecked = e.target.checked;
    setUseSavedResume(isChecked);
    if (isChecked) {
      setSelectedFile(null);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setUseSavedResume(false);
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

    if (selectedFile) {
      formData.append("resume_file", selectedFile);
    }

    const response = await api.post(
      "/recommendations/jobs",
      formData,
      { params }
    );
    setJobs(response.data);
    

    } catch (error) {
    console.error("Recommendation fetch failed", error);
    alert(error.response?.data?.detail || "Something went wrong while fetching jobs.");
    } finally {
    setLoading(false);
    }
  };

  const resetFilters = async () => {
    setDomainId("");
    setLocationId("");
    setExperience("");
    setUseSavedResume(false);
    setSelectedFile(null);
    setLoading(true);
    
    try {
      const formData = new FormData();
      const res = await api.post("/recommendations/jobs", formData);
      setJobs(res.data);
    } catch (error) {
      console.error("Reset failed", error);
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

          <div className="filter-group">
            <label>Resume Recommendation</label>
            <div className="old-resume-checkbox">
              <input 
                type="checkbox" 
                id="useOldResume" 
                checked={useSavedResume} 
                onChange={handleCheckboxChange} 
              />
              <label htmlFor="useOldResume">Apply with saved resume</label>
            </div>

            <div className={`upload-box ${useSavedResume ? "disabled-upload" : ""}`}>
              <input 
                type="file" 
                id="resume-file" 
                accept=".pdf" 
                onChange={handleFileChange}
                disabled={useSavedResume} 
                hidden 
              />
              <button 
                className="browse-btn" 
                disabled={useSavedResume}
                onClick={() => document.getElementById('resume-file').click()}
              >
                Browse
              </button>
              <p>{selectedFile ? selectedFile.name : "Drop a file here"}</p>
              <small>*PDF file supported</small>
            </div>
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

          {loading ? (
            <Loader />
          ) : jobs.length === 0 ? (
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