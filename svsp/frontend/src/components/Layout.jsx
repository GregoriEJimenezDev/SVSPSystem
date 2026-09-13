import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Layout({ title, children }) {
  const { logout, getUser } = useAuth();
  const navigate = useNavigate();
  const user = getUser();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="ios-navbar">
        <span className="ios-navbar__title">{title}</span>
        <div className="ios-navbar__actions">
          <button className="ios-btn ios-btn--secondary ios-btn--sm" onClick={handleLogout}>
            Salir
          </button>
        </div>
      </header>

      <main className="ios-content">{children}</main>

      <nav className="ios-tabbar">
        <NavLink to="/" className={({ isActive }) => `ios-tabbar__item ${isActive ? "active" : ""}`}>
          Inicio
        </NavLink>
        {(user?.role === "adminpro" || user?.modules?.includes("asistencia")) && (
          <NavLink to="/empleados" className={({ isActive }) => `ios-tabbar__item ${isActive ? "active" : ""}`}>
            Asistencia
          </NavLink>
        )}
        {(user?.role === "adminpro" || user?.modules?.includes("visitas")) && (
          <NavLink to="/visitas" className={({ isActive }) => `ios-tabbar__item ${isActive ? "active" : ""}`}>
            Visitas
          </NavLink>
        )}
        {user?.role === "adminpro" && (
          <NavLink to="/usuarios" className={({ isActive }) => `ios-tabbar__item ${isActive ? "active" : ""}`}>
            AdminPRO
          </NavLink>
        )}
      </nav>
    </div>
  );
}
