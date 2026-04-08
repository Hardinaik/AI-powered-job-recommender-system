import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import HomePage from "./pages/HomePage";
import JobListPage from "./pages/JobListPage";
import RecruiterDashBoard from "./pages/RecruiterDashBoard";
import Profile from "./pages/ProfilePage";
import ResetPassword from "./components/auth/ResetPassword"; 

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem("token");
  if (!token) return <Navigate to="/" replace />;
  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/reset-password" element={<ResetPassword />} /> 

        {/* Protected Routes */}
        <Route path="/joblist" element={<ProtectedRoute><JobListPage /></ProtectedRoute>} />
        <Route path="/recruiter-dashboard" element={<ProtectedRoute><RecruiterDashBoard /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;