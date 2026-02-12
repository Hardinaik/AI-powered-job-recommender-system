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
            The Future of Hiring, <br />
            <span>Powered by AI.</span>
          </h1>

          <p className="home-subtitle">
            Our platform uses advanced neural matching to connect elite talent
            with high-growth companies. Choose your path below to get started.
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
