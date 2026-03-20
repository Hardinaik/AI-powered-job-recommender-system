import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Select from "react-select";
import "./ProfilePage.css";
import Logout from "../components/auth/Logout";

export default function JobSeekerProfile() {
  const role = "jobseeker"; 

  const navigate = useNavigate();

  const personalRef = useRef(null);
  const prefRef = useRef(null);
  const securityRef = useRef(null);

  const scrollToSection = (ref) => {
    ref.current?.scrollIntoView({ behavior: "smooth" });
  };

  const [active, setActive] = useState("personal");

  const handleScroll = (section, ref) => {
    setActive(section);
    scrollToSection(ref);
  };

  const [profile] = useState({
    name: "Alex Thompson",
    email: "alex.thompson@design.io",
    phone: "+1 (555) 234-8901",
  });

  const locationOptions = [
    { value: 1, label: "Remote" },
    { value: 2, label: "New York" },
    { value: 3, label: "Austin" },
    { value: 4, label: "San Francisco" },
    { value: 5, label: "London" },
  ];

  const domainOptions = [
    { value: "fintech", label: "FinTech" },
    { value: "saas", label: "SaaS" },
    { value: "edtech", label: "EdTech" },
    { value: "ai", label: "AI/ML" },
  ];

  const [formData, setFormData] = useState({
    location_ids: [],
    domain: null,
    experience: "",
  });

  const handleLocationChange = (selected) => {
    setFormData({
      ...formData,
      location_ids: selected ? selected.map((s) => s.value) : [],
    });
  };

  const handleDomainChange = (selected) => {
    setFormData({
      ...formData,
      domain: selected,
    });
  };

  return (
    <div className="profile-page">

      {/* Top Bar */}
      <div className="top-bar">
        <button
          className="dashboard-btn"
          onClick={() =>
            navigate(role === "jobseeker" ? "/joblist" : "/recruiter-dashboard")
          }
        >
          {role === "jobseeker" ? "Jobs" : "Dashboard"}
        </button>

        <Logout />
      </div>

      <div className="page-body">

        {/* Sidebar */}
        <div className="sidebar">
          <ul>
            <li
              className={active === "personal" ? "active" : ""}
              onClick={() => handleScroll("personal", personalRef)}
            >
              Personal Info
            </li>

            <li
              className={active === "preferences" ? "active" : ""}
              onClick={() => handleScroll("preferences", prefRef)}
            >
              {role === "jobseeker" ? "Preferences" : "Company Info"}
            </li>

            <li
              className={active === "security" ? "active" : ""}
              onClick={() => handleScroll("security", securityRef)}
            >
              Security
            </li>
          </ul>
        </div>

        {/* Main Content */}
        <div className="main-content">

          {/* Profile */}
          <div ref={personalRef} className="card">
            <div className="profile-header">
              <div className="avatar"></div>
              <div>
                <h2>{profile.name}</h2>
              </div>
              <button className="edit-btn">Edit Profile</button>
            </div>

            <div className="profile-details">
              <div>
                <label>Full Name</label>
                <p>{profile.name}</p>
              </div>
              <div>
                <label>Email</label>
                <p>{profile.email}</p>
              </div>
              <div>
                <label>Phone</label>
                <p>{profile.phone}</p>
              </div>
            </div>
          </div>

          {/* Preferences */}
          {role === "jobseeker" && (
            <div ref={prefRef} className="card">
              <div className="middlecard-header">
                <h3>Job Preferences</h3>
                <button className="edit-btn">Edit</button>
              </div>

              <div className="preferences">

                <div className="pref-box">
                  <label>Locations</label>
                  <Select
                    options={locationOptions}
                    isMulti
                    placeholder="Search & select locations..."
                    value={locationOptions.filter((option) =>
                      formData.location_ids.includes(option.value)
                    )}
                    onChange={handleLocationChange}
                    className="react-select"
                    classNamePrefix="select"
                  />
                </div>

                <div className="pref-box">
                  <label>Industry Domain</label>
                  <Select
                    options={domainOptions}
                    placeholder="Select domain"
                    value={formData.domain}
                    onChange={handleDomainChange}
                    className="react-select"
                    classNamePrefix="select"
                  />
                </div>

                <div className="pref-box">
                  <label>Years of Experience</label>
                  <select
                    value={formData.experience}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        experience: e.target.value,
                      })
                    }
                  >
                    <option value="">Select</option>
                    {Array.from({ length: 31 }, (_, i) => (
                      <option key={i} value={i}>
                        {i} years
                      </option>
                    ))}
                  </select>
                </div>

              </div>

              <div className="upload-box">
                <p>Update your Resume (PDF)</p>
                <button className="upload-btn">Browse Files</button>
              </div>
            </div>
          )}

          {role === "recruiter" && (
            <div ref={prefRef} className="card">
              <div className="middlecard-header">
                <h3>Company Information</h3>
                <button className="edit-btn">Edit</button>
              </div>

              <div className="form-group">
                <label>Company Name</label>
                <input type="text" placeholder="Enter company name" />
              </div>

              <div className="form-group">
                <label>Website</label>
                <input type="text" placeholder="Enter website link" />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea placeholder="Enter company description"></textarea>
              </div>
            </div>
          )}

          {/* Security */}
          <div ref={securityRef} className="card">
            <h3>Security & Password</h3>

            <div className="form-group">
              <label>Current Password</label>
              <input type="password" />
            </div>

            <div className="row">
              <div className="form-group">
                <label>New Password</label>
                <input type="password" />
              </div>

              <div className="form-group">
                <label>Confirm Password</label>
                <input type="password" />
              </div>
            </div>

            <button className="save-btn">Save Changes</button>
          </div>

        </div>
      </div>
    </div>
  );
}