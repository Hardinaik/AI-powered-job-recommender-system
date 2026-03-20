
import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import JobListPage from "./pages/JobListPage";
import RecruiterDashboard from "./pages/RecruiterDashBoard";
import JobSeekerProfile from "./pages/ProfilePage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/joblist" element={<JobListPage />} />
        <Route path="/recruiter-dashboard" element={<RecruiterDashboard />} />
        <Route path="/profile" element={<JobSeekerProfile />} />
      </Routes>
    </BrowserRouter>

   
  );
}

export default App;
