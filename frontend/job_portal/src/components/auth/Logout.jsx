import { useNavigate } from "react-router-dom";
import api from "../../api/axios";
import { clearAll } from "../../api/tokenStore";
import "./Logout.css";

function Logout() {
    const navigate = useNavigate();

    const handleLogout = async () => {
        try {
            // Tell server to revoke the refresh token and clear the cookie
            await api.post("/auth/logout");
        } catch {
            // Even if server call fails, clear local state and redirect
        } finally {
            clearAll();
            navigate("/");
        }
    };

    return (
        <button className="logout-btn" onClick={handleLogout}>
            Logout
        </button>
    );
}

export default Logout;