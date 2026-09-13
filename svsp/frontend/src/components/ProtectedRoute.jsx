import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute({ module, children }) {
  const { token, hasModuleAccess } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }
  if (module && !hasModuleAccess(module)) {
    return <Navigate to="/" replace />;
  }
  return children;
}
