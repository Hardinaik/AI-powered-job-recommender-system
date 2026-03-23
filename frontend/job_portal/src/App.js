import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import HomePage from "./pages/HomePage";
import JobListPage from "./pages/JobListPage";
import RecruiterDashboard from "./pages/RecruiterDashBoard";
import Profile from "./pages/ProfilePage";


// Helper: Redirects to "/" if no token is found
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem("token");
  if (!token) {
    return <Navigate to="/" replace />;
  }
  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<HomePage />} />
        
        {/* Protected Routes */}
        <Route 
          path="/joblist" 
          element={<ProtectedRoute><JobListPage /></ProtectedRoute>} 
        />
        <Route 
          path="/recruiter-dashboard" 
          element={<ProtectedRoute><RecruiterDashboard /></ProtectedRoute>} 
        />
        <Route 
          path="/profile" 
          element={<ProtectedRoute><Profile /></ProtectedRoute>} 
        />

        {/* Fallback: Any unknown route goes to Home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;