import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { getSession, logout } from "../services/api";
import "../styles/app.css";

const MODULES = [
  { key: "asistencia", label: "Asistencia", path: "/asistencia" },
  { key: "visitas", label: "Visitas", path: "/visitas" },
  { key: "adminpro", label: "AdminPRO", path: "/adminpro" },
];

export default function Layout({ title, desc, children }) {
  const { modules, email } = getSession();
  const navigate = useNavigate();
  const allowed = MODULES.filter((m) => modules.includes(m.key));

  return (
    <div>
      <header className="topbar">
        <a className="brand" href="/dashboard">
          <span className="brand-mark">S</span> SVSP
        </a>
        <nav className="nav">
          <NavLink to="/dashboard">Panel</NavLink>
          {allowed.map((m) => (
            <NavLink key={m.key} to={m.path}>
              {m.label}
            </NavLink>
          ))}
        </nav>
        <div className="userbox">
          <span>{email}</span>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Salir
          </button>
        </div>
      </header>
      <main className="page">
        <h1>{title}</h1>
        {desc && <p className="desc">{desc}</p>}
        {children}
      </main>
    </div>
  );
}
