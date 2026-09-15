import { Layout } from "../components/Layout";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { getUser } = useAuth();
  const user = getUser();

  return (
    <Layout title="Inicio">
      <h1 className="ios-page-title">Bienvenido</h1>

      <div className="ios-card">
        <div className="ios-list-row">
          <span>Rol</span>
          <span className="ios-badge ios-badge--green">
            {user?.role === "adminpro" ? "AdminPRO" : "Usuario estándar"}
          </span>
        </div>
        <div className="ios-list-row">
          <span>Módulos con acceso</span>
          <span className="ios-list-row__meta">
            {user?.role === "adminpro" ? "Todos" : (user?.modules || []).join(", ") || "Ninguno"}
          </span>
        </div>
      </div>

      <p className="ios-list-group__title">Accesos rápidos</p>
      <div className="ios-card">
        <div className="ios-list-row">
          <span>Sistema de Asistencia</span>
          <span className="ios-list-row__meta">Empleados, reportes y gráficos</span>
        </div>
        <div className="ios-list-row">
          <span>Sistema de Visitas</span>
          <span className="ios-list-row__meta">Registro y verificación por QR</span>
        </div>
      </div>
    </Layout>
  );
}
