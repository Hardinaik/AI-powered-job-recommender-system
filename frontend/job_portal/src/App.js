import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode";
import HomePage from "./pages/HomePage";
import JobListPage from "./pages/JobListPage";
import RecruiterDashBoard from "./pages/RecruiterDashBoard";
import Profile from "./pages/ProfilePage";
import ResetPassword from "./components/auth/ResetPassword";

const isTokenValid = () => {
  const token = localStorage.getItem("token");
  if (!token) return false;

  try {
    const { exp } = jwtDecode(token);
    return Date.now() < exp * 1000;
  } catch {
    return false;
  }
};

const ProtectedRoute = ({ children }) => {
  if (!isTokenValid()) {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    return <Navigate to="/" replace />;
  }
  return children;
};

const RoleRoute = ({ children, allowedRole }) => {
  if (!isTokenValid()) {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    return <Navigate to="/" replace />;
  }

  const role = localStorage.getItem("role");
  if (role !== allowedRole) return <Navigate to="/" replace />;
  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* Jobseeker only */}
        <Route path="/joblist" element={
          <RoleRoute allowedRole="jobseeker"><JobListPage /></RoleRoute>
        } />

        {/* Recruiter only */}
        <Route path="/recruiter-dashboard" element={
          <RoleRoute allowedRole="recruiter"><RecruiterDashBoard /></RoleRoute>
        } />

        {/* Any logged-in user */}
        <Route path="/profile" element={
          <ProtectedRoute><Profile /></ProtectedRoute>
        } />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;