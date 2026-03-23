import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000"
 
});

// Request Interceptor: Attach JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Catch 401s
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token is invalid or expired
      localStorage.removeItem("token");
      window.location.href = "/"; 
    }
    return Promise.reject(error);
  }
);

export default api;