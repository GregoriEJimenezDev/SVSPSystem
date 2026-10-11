import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import Icon from "../components/icons";
import { api, getSession } from "../services/api";

const MODULE_META = {
  asistencia: {
    title: "Asistencia",
    tag: "Control del equipo",
    text: "Importa registros, revisa estadísticas y gestiona justificaciones.",
    icon: "clock",
    tint: "blue",
    path: "/asistencia",
  },
  visitas: {
    title: "Visitas",
    tag: "Accesos externos",
    text: "Registra visitantes y genera códigos QR de verificación.",
    icon: "userPlus",
    tint: "purple",
    path: "/visitas",
  },
  adminpro: {
    title: "AdminPRO",
    tag: "Administración",
    text: "Crea usuarios y controla el acceso a cada módulo.",
    icon: "shield",
    tint: "green",
    path: "/adminpro",
  },
};

const ACTION_LABELS = {
  create_user: "Usuario creado",
  update_user: "Usuario actualizado",
  disable_user: "Usuario inhabilitado",
  change_password: "Contraseña actualizada",
  register_visitor: "Visitante registrado",
  update_visitor: "Visitante actualizado",
  verify_visitor: "Visitante verificado",
  import_excel: "Excel importado",
  create_employee: "Empleado creado",
};

export default function Dashboard() {
  const { modules } = getSession();
  const canAsistencia = modules.includes("asistencia") || modules.includes("adminpro");
  const isAdmin = modules.includes("adminpro");
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");
  const [activity, setActivity] = useState(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!canAsistencia) return;
    api
      .get("/api/v1/attendance/stats")
      .then(setStats)
      .catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!isAdmin) return;
    api
      .get("/api/v1/adminpro/audit-log?limit=6")
      .then(setActivity)
      .catch(() => setActivity([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const kpis = stats
    ? [
        { label: "Total empleados", value: stats.total_employees ?? 0, icon: "users", tint: "blue" },
        { label: "Presentes", value: stats.present_today ?? 0, icon: "check", tint: "green" },
        { label: "Ausentes", value: stats.absent_today ?? 0, icon: "xCircle", tint: "red" },
        { label: "Tardanzas", value: stats.late_today ?? 0, icon: "timer", tint: "amber" },
        { label: "Promedio de horas", value: `${stats.total_hours ?? 0}h`, icon: "chart", tint: "purple" },
      ]
    : [];

  const q = query.trim().toLowerCase();
  const visibleModules = modules.filter((m) => {
    if (!MODULE_META[m]) return false;
    if (!q) return true;
    const meta = MODULE_META[m];
    return (meta.title + " " + meta.text + " " + meta.tag).toLowerCase().includes(q);
  });

  return (
    <Layout
      title="Panel principal"
      onSearch={setQuery}
      searchPlaceholder="Buscar en el panel"
    >
      {error && <div className="alert alert-error">{error}</div>}

      <div className="summary-head">
        <div>
          <h2>Resumen general</h2>
          <p>Consulta el estado de tu organización y accede a tus herramientas.</p>
        </div>
        <Link className="btn btn-primary" to="/asistencia">
          Generar reporte
        </Link>
      </div>

      {canAsistencia && (
        <div className="grid kpis">
          {kpis.map((k) => (
            <div className="card kpi" key={k.label}>
              <div className="kpi-top">
                <span className="kpi-label">{k.label}</span>
                <span className={`icon-badge tint-${k.tint}`}>
                  <Icon name={k.icon} size={17} />
                </span>
              </div>
              <div className="kpi-value">{k.value}</div>
            </div>
          ))}
          {!stats && !error && <p style={{ color: "#8a8a8a" }}>Cargando estadísticas...</p>}
        </div>
      )}

      <div className="panels">
        <section>
          <div className="panels-head">
            <h2>Módulos</h2>
            <span className="link-more">Ver todos</span>
          </div>
          <div className="card module-list">
            {visibleModules.map((m) => {
              const meta = MODULE_META[m];
              return (
                <Link className="module-row" key={m} to={meta.path}>
                  <span className={`icon-badge tint-${meta.tint} lg`}>
                    <Icon name={meta.icon} size={20} />
                  </span>
                  <span className="module-row-body">
                    <span className="module-row-title">
                      {meta.title} <span className="tag">{meta.tag}</span>
                    </span>
                    <span className="module-row-text">{meta.text}</span>
                  </span>
                  <Icon name="chevronRight" size={18} className="chev" />
                </Link>
              );
            })}
            {visibleModules.length === 0 && (
              <p style={{ color: "#8a8a8a", padding: 8 }}>
                {modules.length === 0
                  ? "Tu usuario no tiene módulos asignados. Contacta al AdminPRO."
                  : "Sin resultados para tu búsqueda."}
              </p>
            )}
          </div>
        </section>

        <section>
          <div className="panels-head">
            <h2>Actividad reciente</h2>
          </div>
          <div className="card activity">
            {activity === null ? (
              <div className="activity-empty">
                <span className="icon-badge tint-gray xl">
                  <Icon name="clock" size={22} />
                </span>
                <strong>Sin actividad reciente</strong>
                <p>Los nuevos registros y movimientos aparecerán en este espacio.</p>
              </div>
            ) : activity.length === 0 ? (
              <div className="activity-empty">
                <span className="icon-badge tint-gray xl">
                  <Icon name="clock" size={22} />
                </span>
                <strong>Sin actividad reciente</strong>
                <p>Los nuevos registros y movimientos aparecerán en este espacio.</p>
              </div>
            ) : (
              <ul className="activity-list">
                {activity.map((a) => (
                  <li key={a.id}>
                    <span className="icon-badge tint-navy sm">
                      <Icon name="clock" size={15} />
                    </span>
                    <span>
                      <strong>{ACTION_LABELS[a.action] || a.action}</strong>
                      <small>
                        {(a.details && a.details.email) || a.entity_type || ""} ·{" "}
                        {a.created_at ? new Date(a.created_at).toLocaleString("es") : ""}
                      </small>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>
    </Layout>
  );
}
