/* eslint-disable react-hooks/exhaustive-deps */
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Select from "react-select";
import JobCard from "../components/jobCard";
import Logout from "../components/auth/Logout";
import Loader from "../components/loader";
import api from "../api/axios";
import "./JobListPage.css";
import ErrorBanner from "../components/ErrorBanner";
import { getErrorMessage } from "../utils/errorUtils";

const LIMIT = 20;

function JobListPage() {
  const navigate = useNavigate();
  const [domains, setDomains] = useState([]);
  const [locations, setLocations] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [savedJobIds, setSavedJobIds] = useState([]);
  const [appliedJobIds, setAppliedJobIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);

  // Pagination state
  const [totalJobs, setTotalJobs] = useState(0);
  const [currentSkip, setCurrentSkip] = useState(0);

  // Recommendation state
  const [recommendedJobs, setRecommendedJobs] = useState([]);
  const [isRecommended, setIsRecommended] = useState(false);
  const [rankingMode, setRankingMode] = useState("hybrid");
  const resumeWasIntended = useRef(false);

  // Filter state
  const [useProfile, setUseProfile] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [domainId, setDomainId] = useState("");
  const [selectedLocations, setSelectedLocations] = useState([]);
  const [experience, setExperience] = useState("");
  const [view, setView] = useState("all");

  const isFirstRender = useRef(true);
  const experienceOptions = Array.from({ length: 31 }, (_, i) => i);
  const locationOptions = locations.map((loc) => ({ value: loc.id, label: loc.name }));

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

        await fetchAllJobs(0, false);
      } catch (error) {
        setError(getErrorMessage(error));
        setJobs([]);
      } finally {
        setLoading(false);
      }
    };
    initData();
  }, []);

  // ── 2. View Changes ──
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const fetchViewData = async () => {
      if (view === "all") {
        if (isRecommended) {
          setJobs(Array.isArray(recommendedJobs) ? recommendedJobs : []);
        } else {
          await fetchAllJobs(0, false);
        }
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const endpoint =
          view === "saved"
            ? "/applications/saved-jobs/details"
            : "/applications/applied-jobs/details";

        const res = await api.get(endpoint);
        setJobs(Array.isArray(res.data) ? res.data : []);
      } catch (error) {
        setError(getErrorMessage(error));
        setJobs([]);
      } finally {
        setLoading(false);
      }
    };

    fetchViewData();
  }, [view]);

  // ── Fetch paginated jobs ──
  const fetchAllJobs = async (skip = 0, append = false) => {
    // Use loadingMore for append so the full-page spinner doesn't show
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const res = await api.get("/jobs/all", {
        params: { skip, limit: LIMIT },
      });

      const raw = res.data;

      // Handle both plain array and paginated {total, skip, limit, jobs:[]} shape
      const newJobs = Array.isArray(raw)
        ? raw
        : Array.isArray(raw.jobs)
        ? raw.jobs
        : [];
      const total = raw.total ?? newJobs.length;

      setTotalJobs(total);
      setCurrentSkip(skip + newJobs.length);
      setJobs((prev) => (append ? [...prev, ...newJobs] : newJobs));
    } catch (error) {
      setError(getErrorMessage(error));
      if (!append) setJobs([]);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  // ── Load More handler ──
  const handleLoadMore = () => {
    fetchAllJobs(currentSkip, true);
  };

  // ── Recommendation fetch ──
  const applyFilters = async () => {
    setLoading(true);
    setError(null);
    resumeWasIntended.current = useProfile || !!selectedFile;

    try {
      const formData = new FormData();

      if (!useProfile && selectedFile) {
        formData.append("resume_file", selectedFile);
      }

      const params = { use_profile: useProfile };

      if (!useProfile) {
        if (domainId) params.domain_id = domainId;
        selectedLocations.forEach((loc) => {
          if (!params.location_ids) params.location_ids = [];
          params.location_ids.push(loc.value);
        });
        if (experience !== "") params.experience = experience;
      }

      const response = await api.post("/recommendations/jobs", formData, {
        params,
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

      // Safely extract from recommendation response shape: {ranking_mode, jobs:[]}
      const raw = response.data;
      const resultJobs = Array.isArray(raw)
        ? raw
        : Array.isArray(raw.jobs)
        ? raw.jobs
        : [];
      const ranking_mode = raw.ranking_mode ?? "fallback";

      setRankingMode(ranking_mode);
      setRecommendedJobs(resultJobs);
      setIsRecommended(true);
      setJobs(resultJobs);
      setView("all");
    } catch (error) {
      setError(getErrorMessage(error));
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  // ── Reset filters ──
  const resetFilters = async () => {
    setDomainId("");
    setSelectedLocations([]);
    setExperience("");
    setUseProfile(false);
    setSelectedFile(null);
    setError(null);
    setIsRecommended(false);
    setRecommendedJobs([]);
    setRankingMode("hybrid");
    resumeWasIntended.current = false;
    setTotalJobs(0);
    setCurrentSkip(0);
    setView("all");
    await fetchAllJobs(0, false);
  };

  const handleStatusChange = (jobId, type) => {
    if (type === "save") {
      setSavedJobIds((prev) => [...new Set([...prev, jobId])]);
    } else if (type === "unsave") {
      setSavedJobIds((prev) => prev.filter((id) => id !== jobId));
      if (view === "saved") {
        setJobs((prev) => prev.filter((job) => job.job_id !== jobId));
      }
    } else if (type === "apply") {
      setAppliedJobIds((prev) => [...new Set([...prev, jobId])]);
    }
  };

  const handleProfileToggle = (checked) => {
    setUseProfile(checked);
    if (checked) {
      setDomainId("");
      setSelectedLocations([]);
      setExperience("");
      setSelectedFile(null);
    }
  };

  // ── Ranking mode banner ──
  const getRankingBanner = () => {
    if (!isRecommended || view !== "all") return null;
    if (!resumeWasIntended.current) return null;

    if (rankingMode === "bm25_only") {
      return (
        <ErrorBanner
          message="AI matching is currently unavailable. Showing keyword-based recommendations instead."
          type="warning"
          onClose={() => setRankingMode("hybrid")}
        />
      );
    }

    if (rankingMode === "fallback" && selectedFile !== null) {
      return (
        <ErrorBanner
          message="Recommendation service is unavailable. Showing latest jobs instead."
          type="error"
          onClose={() => setRankingMode("hybrid")}
        />
      );
    }

    return null;
  };

  const viewLabel =
    view === "all"
      ? isRecommended
        ? "Recommended Jobs"
        : "Job Listings"
      : view === "saved"
      ? "Saved Jobs"
      : "Applied Jobs";

  // How many more jobs can be loaded
  const remaining = totalJobs - currentSkip;
  const showLoadMore =
    view === "all" && !isRecommended && !loading && remaining > 0;

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

      <ErrorBanner message={error} onClose={() => setError(null)} />

      {/* ── Body ── */}
      <div className="job-page">

        {/* ── Filters Sidebar ── */}
        <aside className="filters">
          <h3 className="filters-title">Filters</h3>
          <div className="filter-divider" />

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
                Filters &amp; resume will be pulled from your saved profile.
              </p>
            )}
          </div>

          <div className="filter-divider" />

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
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
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
            <button
              className="apply-btn"
              onClick={applyFilters}
              disabled={loading}
            >
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
                {view === "all" && !isRecommended
                  ? `${totalJobs} listing${totalJobs !== 1 ? "s" : ""}`
                  : `${jobs.length} listing${jobs.length !== 1 ? "s" : ""}`}
              </span>
            )}
          </div>

          {/* Ranking mode banner */}
          {getRankingBanner()}

          {loading ? (
            <Loader />
          ) : jobs.length === 0 ? (
            <div className="empty-state">No jobs found</div>
          ) : (
            <>
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

              {/* Load More button */}
              {showLoadMore && (
                <div
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    marginTop: "20px",
                    paddingBottom: "8px",
                  }}
                >
                  <button
                    className="apply-btn"
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                    style={{ padding: "10px 32px", minWidth: "200px" }}
                  >
                    {loadingMore
                      ? "Loading…"
                      : `Load More (${remaining} remaining)`}
                  </button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default JobListPage;