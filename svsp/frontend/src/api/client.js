import axios from "axios";

const API_URL =
  import.meta.env.VITE_API_URL ||
  (window.location.hostname.endsWith(".app.github.dev")
    ? ""
    : "http://localhost:8000");

const apiClient = axios.create({
  baseURL: API_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("svsp_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("svsp_token");
      localStorage.removeItem("svsp_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default apiClient;
