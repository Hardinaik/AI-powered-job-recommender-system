import "./Loader.css";

function Loader() {
  return (
    <div className="loader-container">
      <div className="progress-circle"></div>
      <p className="loader-text">Loading...</p>
    </div>
  );
}

export default Loader;