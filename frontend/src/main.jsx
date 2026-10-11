import React from "react";
import ReactDOM from "react-dom/client";
import {
  createBrowserRouter,
  RouterProvider,
  Navigate,
} from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Asistencia from "./pages/Asistencia";
import Empleados from "./pages/Empleados";
import Justificaciones from "./pages/Justificaciones";
import Visitas from "./pages/Visitas";
import AdminPro from "./pages/AdminPro";
import { getSession } from "./services/api";

function LoginRedirect() {
  React.useEffect(() => {
    window.location.href = "/login.html";
  }, []);
  return (
    <p style={{ padding: 40, fontFamily: "sans-serif" }}>
      Redirigiendo al inicio de sesión...
    </p>
  );
}

function Protected({ modules, children }) {
  const session = getSession();
  if (!session.token) return <Navigate to="/login" replace />;
  if (modules) {
    const ok = modules.some((m) => session.modules.includes(m));
    if (!ok) return <Navigate to="/dashboard" replace />;
  }
  return children;
}

const router = createBrowserRouter([
  { path: "/login", element: <LoginRedirect /> },
  { path: "/", element: <Navigate to="/dashboard" replace /> },
  {
    path: "/dashboard",
    element: (
      <Protected>
        <Dashboard />
      </Protected>
    ),
  },
  {
    path: "/asistencia",
    element: (
      <Protected modules={["asistencia", "adminpro"]}>
        <Asistencia />
      </Protected>
    ),
  },
  {
    path: "/empleados",
    element: (
      <Protected modules={["asistencia", "adminpro"]}>
        <Empleados />
      </Protected>
    ),
  },
  {
    path: "/justificaciones",
    element: (
      <Protected modules={["asistencia", "adminpro"]}>
        <Justificaciones />
      </Protected>
    ),
  },
  {
    path: "/visitas",
    element: (
      <Protected modules={["visitas", "adminpro"]}>
        <Visitas />
      </Protected>
    ),
  },
  {
    path: "/adminpro",
    element: (
      <Protected modules={["adminpro"]}>
        <AdminPro />
      </Protected>
    ),
  },
  { path: "*", element: <Navigate to="/dashboard" replace /> },
]);

ReactDOM.createRoot(document.getElementById("root")).render(
  <RouterProvider router={router} />
);
