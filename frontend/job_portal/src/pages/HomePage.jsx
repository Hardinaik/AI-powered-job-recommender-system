/* eslint-disable react-hooks/exhaustive-deps */
import Login from "../components/auth/Login";
import "./HomePage.css";
import heroImage from "../images/home_img.jpg";

function HomePage() {
  return (
    <div className="home-wrapper">
      <div className="home-grid">
        {/* LEFT */}
        <div className="home-left">
          <h1 className="home-title">
            Find Jobs That <br />
            <span>Match Your Resume.</span>
          </h1>

          <p className="home-subtitle">
            Upload your resume and let our AI instantly match you with the most
            relevant jobs — no endless scrolling, just opportunities built for you.
          </p>

          <img
            src={heroImage}
            alt="AI Hiring"
            className="home-image"
          />
        </div>

        {/* RIGHT */}
        <div className="home-right">
          <Login />
        </div>
      </div>
    </div>
  );
}

export default HomePage;
