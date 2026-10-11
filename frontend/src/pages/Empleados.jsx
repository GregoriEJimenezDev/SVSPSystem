import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import Icon from "../components/icons";
import { api } from "../services/api";

export default function Empleados() {
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [deptFilter, setDeptFilter] = useState("");
  const [search, setSearch] = useState("");
  const [msg, setMsg] = useState({ type: "", text: "" });
  const [loading, setLoading] = useState(false);
  const [empEditId, setEmpEditId] = useState(null);
  const [empForm, setEmpForm] = useState({ name: "", department: "" });
  const [newDept, setNewDept] = useState("");
  const [deptEditId, setDeptEditId] = useState(null);
  const [deptEditName, setDeptEditName] = useState("");
  const [dupGroups, setDupGroups] = useState([]);
  const [mergeSel, setMergeSel] = useState({});

  function loadAll() {
    const empQs = deptFilter ? "?department=" + encodeURIComponent(deptFilter) : "";
    Promise.all([
      api.get("/api/v1/employees/" + empQs),
      api.get("/api/v1/departments/?active_only=false").catch(() => []),
      api.get("/api/v1/employees/duplicates").catch(() => []),
    ])
      .then(([e, d, g]) => {
        setEmployees(e);
        setDepartments(Array.isArray(d) ? d : []);
        setDupGroups(Array.isArray(g) ? g : []);
        setMsg({ type: "", text: "" });
      })
      .catch((e) => setMsg({ type: "error", text: e.message }));
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deptFilter]);

  async function handleEmpEditSave(id) {
    if (!empForm.name.trim()) {
      setMsg({ type: "error", text: "El nombre no puede estar vacío." });
      return;
    }
    setLoading(true);
    try {
      await api.put(`/api/v1/employees/${id}`, {
        name: empForm.name.trim(),
        department: empForm.department || null,
      });
      setMsg({ type: "ok", text: "Empleado actualizado." });
      setEmpEditId(null);
      loadAll();
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
    setLoading(false);
  }

  async function handleDeptCreate(e) {
    e.preventDefault();
    if (!newDept.trim()) return;
    setLoading(true);
    try {
      await api.post("/api/v1/departments/", { name: newDept.trim() });
      setMsg({ type: "ok", text: `Departamento "${newDept.trim()}" creado.` });
      setNewDept("");
      loadAll();
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
    setLoading(false);
  }

  async function handleDeptRename(id) {
    if (!deptEditName.trim()) {
      setMsg({ type: "error", text: "El nombre no puede estar vacío." });
      return;
    }
    setLoading(true);
    try {
      await api.put(`/api/v1/departments/${id}`, { name: deptEditName.trim() });
      setMsg({ type: "ok", text: "Departamento actualizado." });
      setDeptEditId(null);
      loadAll();
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
    setLoading(false);
  }

  async function handleDeptToggle(d) {
    setLoading(true);
    try {
      if (d.is_active) {
        await api.del(`/api/v1/departments/${d.id}`);
        setMsg({ type: "ok", text: "Departamento inhabilitado." });
      } else {
        await api.put(`/api/v1/departments/${d.id}`, { is_active: true });
        setMsg({ type: "ok", text: "Departamento rehabilitado." });
      }
      loadAll();
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
    setLoading(false);
  }

  function toggleMergeSel(groupKey, id) {
    setMergeSel((prev) => {
      const cur = prev[groupKey] || [];
      return {
        ...prev,
        [groupKey]: cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id],
      };
    });
  }

  async function handleMerge(group) {
    const sel = mergeSel[group.key] || [];
    if (sel.length === 0) {
      setMsg({ type: "error", text: "Marca los duplicados a fusionar." });
      return;
    }
    const keepId = group.employees[0].id;
    const dupIds = sel.filter((id) => id !== keepId);
    if (dupIds.length === 0) {
      setMsg({ type: "error", text: "Marca al menos un duplicado distinto al conservado." });
      return;
    }
    setLoading(true);
    try {
      const r = await api.post("/api/v1/employees/merge", { keep_id: keepId, duplicate_ids: dupIds });
      setMsg({
        type: "ok",
        text: `Fusionados: ${r.moved_attendances} asistencias movidas, ${r.deactivated_ids.length} registro(s) inhabilitados.`,
      });
      setMergeSel((prev) => ({ ...prev, [group.key]: [] }));
      loadAll();
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
    setLoading(false);
  }

  const q = search.trim().toLowerCase();
  const filtered = employees.filter((emp) => {
    if (!q) return true;
    return (
      emp.name.toLowerCase().includes(q) ||
      (emp.department || "").toLowerCase().includes(q)
    );
  });

  return (
    <Layout title="Empleados" desc="Gestiona empleados, departamentos y fusiona duplicados.">
      {msg.text && <div className={`alert alert-${msg.type === "ok" ? "ok" : "error"}`}>{msg.text}</div>}

      <div className="card">
        <h2><Icon name="users" size={20} /> Empleados</h2>
        <div className="toolbar">
          <div className="field" style={{ minWidth: 220 }}>
            <label>Departamento</label>
            <select className="input" value={deptFilter} onChange={(e) => setDeptFilter(e.target.value)}>
              <option value="">Todos</option>
              {departments.map((d) => (
                <option key={d.id} value={d.name}>{d.name}</option>
              ))}
            </select>
          </div>
          <div className="field" style={{ minWidth: 220 }}>
            <label>Buscar</label>
            <input className="input" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Nombre o departamento..." />
          </div>
          <button className="btn btn-ghost" onClick={loadAll}>Filtrar</button>
        </div>
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Nombre</th><th>Departamento</th><th>Estado</th><th>Acciones</th></tr></thead>
            <tbody>
              {filtered.map((emp) => (
                <tr key={emp.id}>
                  <td>
                    {empEditId === emp.id ? (
                      <input className="input" value={empForm.name} onChange={(e) => setEmpForm({ ...empForm, name: e.target.value })} />
                    ) : (
                      emp.name
                    )}
                  </td>
                  <td>
                    {empEditId === emp.id ? (
                      <select className="input" value={empForm.department} onChange={(e) => setEmpForm({ ...empForm, department: e.target.value })}>
                        <option value="">— Sin departamento —</option>
                        {departments.filter((d) => d.is_active).map((d) => (
                          <option key={d.id} value={d.name}>{d.name}</option>
                        ))}
                      </select>
                    ) : (
                      emp.department || "—"
                    )}
                  </td>
                  <td>
                    {emp.is_active
                      ? <span className="badge badge-green">Activo</span>
                      : <span className="badge badge-gray">Inactivo</span>}
                  </td>
                  <td style={{ display: "flex", gap: 8 }}>
                    {empEditId === emp.id ? (
                      <React.Fragment>
                        <button className="btn btn-gold btn-sm" disabled={loading} onClick={() => handleEmpEditSave(emp.id)}>Guardar</button>
                        <button className="btn btn-ghost btn-sm" onClick={() => setEmpEditId(null)}>Cancelar</button>
                      </React.Fragment>
                    ) : (
                      <button className="btn btn-ghost btn-sm" onClick={() => {
                        setEmpEditId(emp.id);
                        setEmpForm({ name: emp.name, department: emp.department || "" });
                      }}>
                        <Icon name="pencil" size={14} /> Editar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan="4" style={{ color: "#8a8a8a" }}>Sin empleados. Importa el Excel del ponchador para comenzar.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {dupGroups.length > 0 && (
        <div className="card">
          <h2><Icon name="users" size={20} /> Posibles duplicados</h2>
          <p style={{ color: "#8a8a8a", marginBottom: 12 }}>
            Mismo nombre normalizado. Se conserva el primero de cada grupo; los marcados se inhabilitan y sus registros pasan al conservado.
          </p>
          {dupGroups.map((g) => (
            <div key={g.key} style={{ borderTop: "1px solid #eef1f6", padding: "10px 0" }}>
              <strong style={{ textTransform: "capitalize" }}>{g.key}</strong>
              {g.employees.map((m, i) => (
                <label key={m.id} style={{ display: "flex", gap: 8, alignItems: "center", padding: "4px 0" }}>
                  <input
                    type="checkbox"
                    disabled={i === 0}
                    checked={(mergeSel[g.key] || []).includes(m.id)}
                    onChange={() => toggleMergeSel(g.key, m.id)}
                  />
                  <span>{m.name} — {m.department || "sin depto"} {i === 0 ? "(se conserva)" : ""} {!m.is_active ? "(inactivo)" : ""}</span>
                </label>
              ))}
              <button className="btn btn-gold btn-sm" disabled={loading} onClick={() => handleMerge(g)} style={{ marginTop: 6 }}>
                Fusionar marcados
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <h2><Icon name="grid" size={20} /> Departamentos</h2>
        <form onSubmit={handleDeptCreate} style={{ display: "flex", gap: 10, marginBottom: 14 }}>
          <input className="input" value={newDept} onChange={(e) => setNewDept(e.target.value)}
            placeholder="Nombre del departamento" style={{ maxWidth: 320 }} />
          <button className="btn btn-gold" disabled={loading}>
            <Icon name="plus" size={16} /> Crear
          </button>
        </form>
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Nombre</th><th>Estado</th><th>Acciones</th></tr></thead>
            <tbody>
              {departments.map((d) => (
                <tr key={d.id}>
                  <td>
                    {deptEditId === d.id ? (
                      <input className="input" value={deptEditName} onChange={(e) => setDeptEditName(e.target.value)} />
                    ) : (
                      d.name
                    )}
                  </td>
                  <td>
                    {d.is_active
                      ? <span className="badge badge-green">Activo</span>
                      : <span className="badge badge-gray">Inactivo</span>}
                  </td>
                  <td style={{ display: "flex", gap: 8 }}>
                    {deptEditId === d.id ? (
                      <React.Fragment>
                        <button className="btn btn-gold btn-sm" disabled={loading} onClick={() => handleDeptRename(d.id)}>Guardar</button>
                        <button className="btn btn-ghost btn-sm" onClick={() => setDeptEditId(null)}>Cancelar</button>
                      </React.Fragment>
                    ) : (
                      <React.Fragment>
                        <button className="btn btn-ghost btn-sm" onClick={() => { setDeptEditId(d.id); setDeptEditName(d.name); }}>
                          <Icon name="pencil" size={14} /> Renombrar
                        </button>
                        <button className="btn btn-ghost btn-sm" onClick={() => handleDeptToggle(d)}>
                          {d.is_active ? "Inhabilitar" : "Rehabilitar"}
                        </button>
                      </React.Fragment>
                    )}
                  </td>
                </tr>
              ))}
              {departments.length === 0 && (
                <tr><td colSpan="3" style={{ color: "#8a8a8a" }}>Sin departamentos. Crea el primero arriba.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
