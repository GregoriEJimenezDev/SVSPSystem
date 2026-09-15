import { Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import AdminUsers from "./pages/AdminUsers";
import Dashboard from "./pages/Dashboard";
import Employees from "./pages/Employees";
import Login from "./pages/Login";
import Visitors from "./pages/Visitors";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/empleados"
        element={
          <ProtectedRoute module="asistencia">
            <Employees />
          </ProtectedRoute>
        }
      />
      <Route
        path="/visitas"
        element={
          <ProtectedRoute module="visitas">
            <Visitors />
          </ProtectedRoute>
        }
      />
      <Route
        path="/usuarios"
        element={
          <ProtectedRoute>
            <AdminUsers />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
