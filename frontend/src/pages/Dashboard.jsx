import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import { api, getSession } from "../services/api";

const CARDS = {
  asistencia: { icon: "📋", title: "Asistencia", text: "Importar Excel del ponchador, ver estadísticas, justificaciones y QR del reporte.", path: "/asistencia" },
  visitas: { icon: "🚶", title: "Visitas", text: "Registrar visitantes, generar QR de verificación y controlar ingresos.", path: "/visitas" },
  adminpro: { icon: "🛡️", title: "AdminPRO", text: "Crear usuarios y asignar a qué módulos puede entrar cada uno.", path: "/adminpro" },
};

export default function Dashboard() {
  const { modules } = getSession();
  const canAsistencia = modules.includes("asistencia") || modules.includes("adminpro");
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!canAsistencia) return;
    api
      .get("/api/v1/attendance/stats")
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  const kpis = stats
    ? [
        { label: "Total Empleados", value: stats.total_employees },
        { label: "Presentes", value: stats.present_today },
        { label: "Ausentes", value: stats.absent_today },
        { label: "Tardanzas", value: stats.late_today },
        { label: "Promedio Horas", value: stats.total_hours },
      ]
    : [];

  return (
    <Layout title="Panel Principal" desc="Resumen general y acceso a tus módulos.">
      {error && <div className="alert alert-error">{error}</div>}
      {canAsistencia && (
        <div className="grid kpis">
          {kpis.map((k) => (
            <div className="card kpi" key={k.label} style={{ marginBottom: 0 }}>
              <div className="label">{k.label}</div>
              <div className="value">{k.value}</div>
            </div>
          ))}
          {!stats && !error && <p style={{ color: "#8a8a8a" }}>Cargando estadísticas...</p>}
        </div>
      )}
      <div className="module-cards">
        {modules.map((m) =>
          CARDS[m] ? (
            <Link className="card module-card" key={m} to={CARDS[m].path}>
              <div className="icon">{CARDS[m].icon}</div>
              <h3>{CARDS[m].title}</h3>
              <p>{CARDS[m].text}</p>
            </Link>
          ) : null
        )}
        {modules.length === 0 && <p style={{ color: "#8a8a8a" }}>Tu usuario no tiene módulos asignados. Contacta al AdminPRO.</p>}
      </div>
    </Layout>
  );
}
