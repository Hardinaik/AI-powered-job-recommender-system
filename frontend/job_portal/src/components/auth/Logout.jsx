import { useNavigate } from "react-router-dom";
import "./Logout.css"

function Logout() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    navigate("/");
  };

  return (
    <button className="logout-btn" onClick={handleLogout}>
        Logout
    </button>
  );
}

export default Logout;