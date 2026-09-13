import { createContext, useContext, useState } from "react";
import apiClient from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("svsp_token"));

  async function login(email, password) {
    const response = await apiClient.post("/api/auth/login", { email, password });
    const accessToken = response.data.access_token;
    localStorage.setItem("svsp_token", accessToken);
    setToken(accessToken);

    const payload = JSON.parse(atob(accessToken.split(".")[1]));
    const user = { role: payload.role, modules: payload.modules || [] };
    localStorage.setItem("svsp_user", JSON.stringify(user));
    return user;
  }

  function logout() {
    localStorage.removeItem("svsp_token");
    localStorage.removeItem("svsp_user");
    setToken(null);
  }

  function getUser() {
    const raw = localStorage.getItem("svsp_user");
    return raw ? JSON.parse(raw) : null;
  }

  function hasModuleAccess(module) {
    const user = getUser();
    if (!user) return false;
    return user.role === "adminpro" || (user.modules || []).includes(module);
  }

  return (
    <AuthContext.Provider value={{ token, login, logout, getUser, hasModuleAccess }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
