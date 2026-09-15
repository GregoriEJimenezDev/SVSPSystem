import { useEffect, useState } from "react";
import apiClient from "../api/client";
import { Layout } from "../components/Layout";

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("standard");
  const [modules, setModules] = useState([]);
  const [error, setError] = useState("");

  async function loadUsers() {
    const res = await apiClient.get("/api/users/");
    setUsers(res.data);
  }

  useEffect(() => {
    loadUsers();
  }, []);

  function toggleModule(mod) {
    setModules((prev) => (prev.includes(mod) ? prev.filter((m) => m !== mod) : [...prev, mod]));
  }

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    try {
      await apiClient.post("/api/users/", {
        full_name: fullName,
        email,
        password,
        role,
        modules: role === "adminpro" ? ["asistencia", "visitas"] : modules,
      });
      setFullName("");
      setEmail("");
      setPassword("");
      setRole("standard");
      setModules([]);
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo crear el usuario.");
    }
  }

  async function handleToggleActive(user) {
    await apiClient.put(`/api/users/${user.id}`, { is_active: !user.is_active });
    loadUsers();
  }

  return (
    <Layout title="AdminPRO">
      <h1 className="ios-page-title">Usuarios del sistema</h1>

      <p className="ios-list-group__title">Crear nuevo usuario</p>
      <form className="ios-card" style={{ padding: 16 }} onSubmit={handleCreate}>
        <input
          className="ios-input"
          placeholder="Nombre completo"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
        />
        <input
          className="ios-input"
          type="email"
          placeholder="Correo"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="ios-input"
          type="password"
          placeholder="Contraseña temporal"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <label className="ios-label">Rol</label>
        <select className="ios-input" value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="standard">Usuario estándar</option>
          <option value="adminpro">AdminPRO (acceso total)</option>
        </select>

        {role === "standard" && (
          <>
            <label className="ios-label">Módulos permitidos</label>
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              <button
                type="button"
                className={`ios-btn ios-btn--sm ${modules.includes("asistencia") ? "ios-btn--primary" : "ios-btn--secondary"}`}
                onClick={() => toggleModule("asistencia")}
              >
                Asistencia
              </button>
              <button
                type="button"
                className={`ios-btn ios-btn--sm ${modules.includes("visitas") ? "ios-btn--primary" : "ios-btn--secondary"}`}
                onClick={() => toggleModule("visitas")}
              >
                Visitas
              </button>
            </div>
          </>
        )}

        {error && <p className="ios-error-text">{error}</p>}

        <button className="ios-btn ios-btn--primary" style={{ width: "100%" }}>
          Crear usuario
        </button>
      </form>

      <p className="ios-list-group__title">Usuarios existentes</p>
      <div className="ios-card">
        {users.map((u) => (
          <div className="ios-list-row" key={u.id}>
            <div>
              <div>{u.full_name}</div>
              <div className="ios-list-row__meta">
                {u.email} · {u.role === "adminpro" ? "AdminPRO" : (u.modules || []).join(", ") || "Sin módulos"}
              </div>
            </div>
            <button
              className={`ios-btn ios-btn--sm ${u.is_active ? "ios-btn--danger" : "ios-btn--secondary"}`}
              onClick={() => handleToggleActive(u)}
            >
              {u.is_active ? "Inhabilitar" : "Rehabilitar"}
            </button>
          </div>
        ))}
      </div>
    </Layout>
  );
}
