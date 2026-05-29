import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode";
import api from "./api/axios";
import { getAccessToken, setAccessToken, setUserRole, getUserRole } from "./api/tokenStore";
import Loader from "./components/loader";
import HomePage from "./pages/HomePage";
import JobListPage from "./pages/JobListPage";
import RecruiterDashBoard from "./pages/RecruiterDashBoard";
import Profile from "./pages/ProfilePage";
import ResetPassword from "./components/auth/ResetPassword";

const isTokenValid = () => {
  const token = getAccessToken();
  if (!token) return false;
  try {
    const { exp } = jwtDecode(token);
    return Date.now() < exp * 1000;
  } catch {
    return false;
  }
};

const ProtectedRoute = ({ children }) => {
  if (!isTokenValid()) return <Navigate to="/" replace />;
  return children;
};

const RoleRoute = ({ children, allowedRole }) => {
  if (!isTokenValid()) return <Navigate to="/" replace />;
  if (getUserRole() !== allowedRole) return <Navigate to="/" replace />;
  return children;
};

function App() {
  // null = still checking, false = no session, true = session restored
  const [authReady, setAuthReady] = useState(null);

  useEffect(() => {
    // If there's already a valid in-memory token, nothing to do
    if (isTokenValid()) {
      setAuthReady(true);
      return;
    }

    // Otherwise try the HttpOnly cookie refresh
    api.post("/auth/refresh")
      .then((res) => {
        setAccessToken(res.data.access_token);
        // Decode role from the new token
        const { role } = jwtDecode(res.data.access_token);
        setUserRole(role);
        setAuthReady(true);
      })
      .catch(() => {
        // No valid cookie — user is genuinely logged out
        setAuthReady(false);
      });
  }, []);

  if (authReady === null) return <Loader />;

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/joblist" element={
          <RoleRoute allowedRole="jobseeker"><JobListPage /></RoleRoute>
        } />
        <Route path="/recruiter-dashboard" element={
          <RoleRoute allowedRole="recruiter"><RecruiterDashBoard /></RoleRoute>
        } />
        <Route path="/profile" element={
          <ProtectedRoute><Profile /></ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;