import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { getSession, logout } from "../services/api";
import Icon from "./icons";
import "../styles/app.css";

const MODULES = [
  { key: "panel", label: "Panel", path: "/dashboard", icon: "grid", always: true },
  { key: "asistencia", label: "Asistencia", path: "/asistencia", icon: "clock" },
  { key: "asistencia", label: "Empleados", path: "/empleados", icon: "users" },
  { key: "asistencia", label: "Justificaciones", path: "/justificaciones", icon: "memo" },
  { key: "visitas", label: "Visitas", path: "/visitas", icon: "userPlus" },
  { key: "adminpro", label: "AdminPRO", path: "/adminpro", icon: "shield" },
];

function initials(email) {
  const s = (email || "?").trim();
  return s.slice(0, 2).toUpperCase();
}

function todayEs() {
  const s = new Date().toLocaleDateString("es", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export default function Layout({ title, desc, children, onSearch, searchPlaceholder }) {
  const { modules, email } = getSession();
  const navigate = useNavigate();
  const allowed = MODULES.filter((m) => m.always || modules.includes(m.key));
  const roleLabel = modules.includes("adminpro")
    ? "Acceso completo"
    : modules.join(", ") || "Sin módulos";

  return (
    <div className="shell">
      <aside className="sidebar">
        <a className="side-brand" href="/dashboard">
          <span className="side-brand-mark">S</span>
          <span>
            <strong>SVSP</strong>
            <small>Control de asistencia</small>
          </span>
        </a>
        <p className="side-section">Espacio de trabajo</p>
        <nav className="side-nav">
          {allowed.map((m) => (
            <NavLink
              key={m.key}
              to={m.path}
              className={({ isActive }) => `side-link${isActive ? " active" : ""}`}
            >
              <Icon name={m.icon} size={19} />
              {m.label}
            </NavLink>
          ))}
        </nav>
        <div className="side-user">
          <span className="side-avatar">{initials(email)}</span>
          <span className="side-user-info">
            <strong>{email}</strong>
            <small>{roleLabel}</small>
          </span>
          <button
            className="icon-btn"
            title="Cerrar sesión"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            <Icon name="logout" size={17} />
          </button>
        </div>
      </aside>

      <div className="shell-main">
        <header className="apptopbar">
          <div>
            {title && <h1>{title}</h1>}
            {desc ? <p>{desc}</p> : <p>{todayEs()}</p>}
          </div>
          <div className="apptopbar-right">
            {onSearch && (
              <label className="appsearch">
                <Icon name="search" size={16} />
                <input
                  placeholder={searchPlaceholder || "Buscar en el panel"}
                  onChange={(e) => onSearch(e.target.value)}
                />
                <kbd>⌘K</kbd>
              </label>
            )}
            <span className="status-pill">
              <span className="dot" />
              Sistema activo
            </span>
          </div>
        </header>
        <main className="page">{children}</main>
      </div>
    </div>
  );
}
