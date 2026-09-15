import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import { api } from "../services/api";

const ALL_MODULES = [
  { key: "asistencia", label: "Asistencia" },
  { key: "visitas", label: "Visitas" },
  { key: "adminpro", label: "AdminPRO" },
];

const EMPTY = { email: "", full_name: "", password: "", modules: ["asistencia"], is_active: true };

export default function AdminPro() {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState(null);
  const [msg, setMsg] = useState({ type: "", text: "" });
  const [loading, setLoading] = useState(false);

  function load() {
    api
      .get("/api/v1/adminpro/users")
      .then(setUsers)
      .catch((e) => setMsg({ type: "error", text: e.message }));
  }

  useEffect(() => {
    load();
  }, []);

  function toggleModule(key) {
    setForm((f) => ({
      ...f,
      modules: f.modules.includes(key)
        ? f.modules.filter((m) => m !== key)
        : [...f.modules, key],
    }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (form.modules.length === 0) {
      setMsg({ type: "error", text: "Asigna al menos un módulo al usuario." });
      return;
    }
    setLoading(true);
    try {
      if (editingId) {
        const payload = { full_name: form.full_name, modules: form.modules, is_active: form.is_active };
        await api.put(`/api/v1/adminpro/users/${editingId}`, payload);
        setMsg({ type: "ok", text: "Usuario actualizado." });
      } else {
        if (form.password.length < 8) {
          setMsg({ type: "error", text: "La contraseña debe tener al menos 8 caracteres." });
          setLoading(false);
          return;
        }
        await api.post("/api/v1/adminpro/users", form);
        setMsg({ type: "ok", text: `Usuario ${form.email} creado con acceso a: ${form.modules.join(", ")}.` });
      }
      setForm(EMPTY);
      setEditingId(null);
      load();
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
    setLoading(false);
  }

  function handleEdit(u) {
    setEditingId(u.id);
    setForm({ email: u.email, full_name: u.full_name, password: "", modules: u.modules || [], is_active: u.is_active });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleToggleActive(u) {
    try {
      await api.put(`/api/v1/adminpro/users/${u.id}`, { is_active: !u.is_active });
      setMsg({ type: "ok", text: u.is_active ? "Usuario inhabilitado." : "Usuario rehabilitado." });
      load();
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
  }

  return (
    <Layout title="AdminPRO" desc="Crea usuarios del sistema y decide a qué módulos puede entrar cada uno.">
      {msg.text && <div className={`alert alert-${msg.type === "ok" ? "ok" : "error"}`}>{msg.text}</div>}

      <div className="card">
        <h2>{editingId ? "✏️ Editar usuario" : "➕ Crear usuario"}</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="field">
              <label>Correo electrónico</label>
              <input className="input" type="email" required disabled={!!editingId} value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="usuario@empresa.com" />
            </div>
            <div className="field">
              <label>Nombre completo</label>
              <input className="input" required value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="Nombre y apellido" />
            </div>
            {!editingId && (
              <div className="field">
                <label>Contraseña (mín. 8 caracteres)</label>
                <input className="input" type="password" required value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="••••••••" />
              </div>
            )}
          </div>
          <div className="field" style={{ marginBottom: 16 }}>
            <label>Módulos a los que puede entrar</label>
            <div className="checks">
              {ALL_MODULES.map((m) => (
                <label key={m.key}>
                  <input type="checkbox" checked={form.modules.includes(m.key)} onChange={() => toggleModule(m.key)} />
                  {m.label}
                </label>
              ))}
            </div>
            <p style={{ fontSize: 13, color: "#8a8a8a", marginTop: 8 }}>
              Ej.: solo <b>Asistencia</b> para el encargado del ponchador, solo <b>Visitas</b> para recepción, o ambos. Solo <b>AdminPRO</b> entra aquí.
            </p>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn btn-gold" disabled={loading}>
              {loading ? "Guardando..." : editingId ? "Guardar cambios" : "Crear usuario"}
            </button>
            {editingId && (
              <button type="button" className="btn btn-ghost" onClick={() => { setEditingId(null); setForm(EMPTY); }}>
                Cancelar
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="card">
        <h2>👥 Usuarios del sistema</h2>
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Correo</th><th>Nombre</th><th>Módulos</th><th>Estado</th><th>Acciones</th></tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.email}</td>
                  <td>{u.full_name}</td>
                  <td>
                    {(u.modules || []).map((m) => (
                      <span key={m} className="badge badge-gold" style={{ marginRight: 6 }}>{m}</span>
                    ))}
                  </td>
                  <td>
                    {u.is_active
                      ? <span className="badge badge-green">Activo</span>
                      : <span className="badge badge-red">Inactivo</span>}
                  </td>
                  <td style={{ display: "flex", gap: 8 }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleEdit(u)}>Editar</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleToggleActive(u)}>
                      {u.is_active ? "Inhabilitar" : "Rehabilitar"}
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan="5" style={{ color: "#8a8a8a" }}>Sin usuarios.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
