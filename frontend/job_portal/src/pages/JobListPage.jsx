import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Select from "react-select";
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

  // --- Filter state ---
  const [useProfile, setUseProfile] = useState(false);       // "Recommend using profile" checkbox
  const [selectedFile, setSelectedFile] = useState(null);    // manual resume upload
  const [domainId, setDomainId] = useState("");
  const [selectedLocations, setSelectedLocations] = useState([]); // [{ value, label }, ...]
  const [experience, setExperience] = useState("");

  const [view, setView] = useState("all");

  const experienceOptions = Array.from({ length: 31 }, (_, i) => i);

  // react-select options derived from locations list
  const locationOptions = locations.map((loc) => ({
    value: loc.id,
    label: loc.name,
  }));

  // ── 1. Initial Load ──
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

  // ── 2. View Changes ──
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
      const formData = new FormData();
      formData.append("use_profile", useProfile);

      // Manual resume upload — only relevant when profile mode is OFF
      if (!useProfile && selectedFile) {
        formData.append("resume_file", selectedFile);
      }

      // Query params — only sent in manual mode
      // In profile mode the backend reads these from the saved profile itself
      const params = {};
      if (!useProfile) {
        if (domainId) params.domain_id = domainId;
        // Send each selected location as a repeated param: ?location_ids=1&location_ids=2
        selectedLocations.forEach((loc) => {
          if (!params.location_ids) params.location_ids = [];
          params.location_ids.push(loc.value);
        });
        if (experience !== "") params.experience = experience;
      }

      const response = await api.post("/recommendations/jobs", formData, {
        params,
        // axios serialises repeated array params correctly with this setting
        paramsSerializer: (p) => {
          const parts = [];
          Object.entries(p).forEach(([key, val]) => {
            if (Array.isArray(val)) {
              val.forEach((v) => parts.push(`${key}=${v}`));
            } else {
              parts.push(`${key}=${val}`);
            }
          });
          return parts.join("&");
        },
      });

      setJobs(response.data);
    } catch (error) {
      console.error("Fetch failed", error);
    } finally {
      setLoading(false);
    }
  };

  const resetFilters = async () => {
    setDomainId("");
    setSelectedLocations([]);
    setExperience("");
    setUseProfile(false);
    setSelectedFile(null);

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("use_profile", false);
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

  // When profile mode is toggled on, clear manual filter state (and vice-versa)
  const handleProfileToggle = (checked) => {
    setUseProfile(checked);
    if (checked) {
      setDomainId("");
      setSelectedLocations([]);
      setExperience("");
      setSelectedFile(null);
    }
  };

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

          {/* ── Recommend using profile ── */}
          <div className="filter-group">
            <div className="profile-rec-checkbox">
              <input
                type="checkbox"
                id="useProfile"
                checked={useProfile}
                onChange={(e) => handleProfileToggle(e.target.checked)}
              />
              <label htmlFor="useProfile">Recommend using profile</label>
            </div>
            {useProfile && (
              <p className="profile-rec-hint">
                Filters & resume will be pulled from your saved profile.
              </p>
            )}
          </div>

          <div className="filter-divider" />

          {/* ── Manual filters — disabled when profile mode is on ── */}
          <div className={useProfile ? "filters-manual disabled-filters" : "filters-manual"}>

            <div className="filter-group">
              <label>Industry Domain</label>
              <select
                value={domainId}
                onChange={(e) => setDomainId(e.target.value)}
                disabled={useProfile}
              >
                <option value="">All Domains</option>
                {domains.map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Locations</label>
              <Select
                options={locationOptions}
                isMulti
                isDisabled={useProfile}
                placeholder="Search & select locations…"
                value={selectedLocations}
                onChange={(selected) => setSelectedLocations(selected || [])}
                className="react-select-container"
                classNamePrefix="rselect"
              />
            </div>

            <div className="filter-group">
              <label>Experience (Years)</label>
              <select
                value={experience}
                onChange={(e) => setExperience(e.target.value)}
                disabled={useProfile}
              >
                <option value="">Any Experience</option>
                {experienceOptions.map((exp) => (
                  <option key={exp} value={exp}>
                    {exp === 0 ? "Fresher (0 years)" : `${exp} year${exp > 1 ? "s" : ""}`}
                  </option>
                ))}
              </select>

            </div>

            {/* Resume upload — manual mode only, no DB save */}
            <div className="filter-group">
              <label>Resume (optional)</label>
              <div className="upload-box">
                <input
                  type="file"
                  id="resume-file"
                  accept=".pdf"
                  onChange={(e) => setSelectedFile(e.target.files[0])}
                  disabled={useProfile}
                  hidden
                />
                <button
                  className="browse-btn"
                  disabled={useProfile}
                  onClick={() => document.getElementById("resume-file").click()}
                >
                  Browse Files
                </button>
                <p>{selectedFile ? selectedFile.name : "PDF, max 5 MB"}</p>
              </div>
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
              <span className="job-list-badge">
                {jobs.length} listing{jobs.length !== 1 ? "s" : ""}
              </span>
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