import React, { useEffect, useState, useCallback } from "react";
import Layout from "../components/Layout";
import { api } from "../services/api";
import Icon from "../components/icons";

function Donut({ present, absent, late }) {
  const total = present + absent + late || 1;
  const pP = (present / total) * 100;
  const pA = (absent / total) * 100;
  const R = 54;
  const C = 2 * Math.PI * R;
  return (
    <div className="donut-wrap">
      <svg width="150" height="150" viewBox="0 0 150 150">
        <circle cx="75" cy="75" r={R} fill="none" stroke="#eee7d2" strokeWidth="18" />
        <circle cx="75" cy="75" r={R} fill="none" stroke="#1e7e34" strokeWidth="18"
          strokeDasharray={`${(pP / 100) * C} ${C}`} transform="rotate(-90 75 75)" />
        <circle cx="75" cy="75" r={R} fill="none" stroke="#b91c1c" strokeWidth="18"
          strokeDasharray={`${(pA / 100) * C} ${C}`} strokeDashoffset={-((pP / 100) * C)} transform="rotate(-90 75 75)" />
        <text x="75" y="82" textAnchor="middle" fontSize="22" fontWeight="800" fill="#2c2c2c">{present + absent + late}</text>
      </svg>
      <div className="legend">
        <div><span className="dot" style={{ background: "#1e7e34" }} />Presentes: {present}</div>
        <div><span className="dot" style={{ background: "#b91c1c" }} />Ausentes: {absent}</div>
        <div><span className="dot" style={{ background: "#b8912f" }} />Tarde: {late}</div>
      </div>
    </div>
  );
}

export default function Asistencia() {
  const [stats, setStats] = useState(null);
  const [chart, setChart] = useState(null);
  const [rows, setRows] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [filters, setFilters] = useState({ employee_id: "", department: "", start_date: "", end_date: "" });
  const [departments, setDepartments] = useState([]);
  const [empEditId, setEmpEditId] = useState(null);
  const [empForm, setEmpForm] = useState({ name: "", department: "" });
  const [newDept, setNewDept] = useState("");
  const [deptEditId, setDeptEditId] = useState(null);
  const [deptEditName, setDeptEditName] = useState("");
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState({ type: "", text: "" });
  const [loading, setLoading] = useState(false);
  const [qr, setQr] = useState(null);
  const [justifs, setJustifs] = useState([]);
  const [justForm, setJustForm] = useState({ employee_id: "", type: "permiso", description: "", start_date: "", end_date: "" });
  const [dragOver, setDragOver] = useState(false);

  function loadAll() {
    const q = new URLSearchParams();
    if (filters.employee_id) q.append("employee_id", filters.employee_id);
    if (filters.start_date) q.append("start_date", filters.start_date);
    if (filters.end_date) q.append("end_date", filters.end_date);
    if (filters.department) q.append("department", filters.department);
    const qs = q.toString() ? "?" + q.toString() : "";
    const empQs = filters.department ? "?department=" + encodeURIComponent(filters.department) : "";
    Promise.all([
      api.get("/api/v1/attendance/stats" + qs),
      api.get("/api/v1/attendance/chart-data" + qs),
      api.get("/api/v1/attendance/" + qs),
      api.get("/api/v1/employees/" + empQs),
      api.get("/api/v1/departments/").catch(() => []),
    ])
      .then(([s, c, r, e, d]) => {
        setStats(s);
        setChart(c);
        setRows(r);
        setEmployees(e);
        setDepartments(Array.isArray(d) ? d : []);
        setMsg({ type: "", text: "" });
      })
      .catch((e) => setMsg({ type: "error", text: e.message }));
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleImport(e) {
    e.preventDefault();
    if (!file) {
      setMsg({ type: "error", text: "Selecciona un archivo." });
      return;
    }
    setLoading(true);
    try {
      const r = await api.upload("/api/v1/attendance/import-excel", file);
      setMsg({
        type: "ok",
        text: `Importación completa: ${r.processed} procesados, ${r.created} empleados nuevos, ${r.updated} actualizados.` +
          (r.errors && r.errors.length ? ` Errores: ${r.errors.length}.` : ""),
      });
      setFile(null);
      loadAll();
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
    setLoading(false);
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      setFile(files[0]);
      setMsg({ type: "", text: "" });
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  function reportPayload() {
    const payload = {};
    if (filters.employee_id) payload.employee_id = Number(filters.employee_id);
    if (filters.department) payload.department = filters.department;
    if (filters.start_date) payload.start_date = filters.start_date;
    if (filters.end_date) payload.end_date = filters.end_date;
    return payload;
  }

  async function handleQR() {
    setLoading(true);
    try {
      const r = await api.post("/api/v1/attendance/report-qr", reportPayload());
      setQr(r);
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
    setLoading(false);
  }

  async function handleDocx() {
    setLoading(true);
    try {
      const { blob, filename } = await api.download("/api/v1/attendance/report-docx", reportPayload());
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);
      setMsg({ type: "ok", text: `Reporte Word descargado: ${filename}` });
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
    setLoading(false);
  }

  async function handleEmpEditSave(id) {
    if (!empForm.name.trim()) {
      setMsg({ type: "error", text: "El nombre no puede estar vacío." });
      return;
    }
    setLoading(true);
    try {
      await api.put(`/api/v1/employees/${id}`, {
        name: empForm.name.trim(),
        department: empForm.department.trim() || null,
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

  async function loadJustifs(employeeId) {
    if (!employeeId) {
      setJustifs([]);
      return;
    }
    try {
      setJustifs(await api.get(`/api/v1/justifications/employee/${employeeId}`));
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  async function handleJustify(e) {
    e.preventDefault();
    try {
      await api.post("/api/v1/justifications/", {
        ...justForm,
        employee_id: Number(justForm.employee_id),
      });
      setMsg({ type: "ok", text: "Justificación registrada." });
      setJustForm({ employee_id: "", type: "permiso", description: "", start_date: "", end_date: "" });
      setJustifs([]);
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
  }

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
    <Layout title="Módulo de Asistencia" desc="Importa el Excel del ponchador, consulta registros, justifica y genera el QR del reporte.">
      {msg.text && <div className={`alert alert-${msg.type === "ok" ? "ok" : "error"}`}>{msg.text}</div>}

      <div className="grid kpis">
        {kpis.map((k) => (
          <div className="card kpi" key={k.label} style={{ marginBottom: 0 }}>
            <div className="label">{k.label}</div>
            <div className="value">{k.value}</div>
          </div>
        ))}
      </div>

      <div className={`card ${dragOver ? "drop-active" : ""}`}
          onDrop={handleDrop} onDragOver={handleDragOver} onDragLeave={handleDragLeave}>
        <h2><Icon name="upload" size={20} /> Importar Excel del ponchador</h2>
        <form onSubmit={handleImport} className="toolbar">
          <div className="field">
            <label>Archivo .xls o .xlsx</label>
            <input className="input" type="file" accept=".xls,.xlsx,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              onChange={(e) => setFile(e.target.files[0])}
              style={{ display: "none" }} id="fileInput" />
            <label htmlFor="fileInput" className="drop-zone-label">
              {file ? file.name : "Arrastra cualquier archivo aquí o haz clic"}
            </label>
          </div>
          <button className="btn btn-gold" disabled={loading}>
            {loading ? "Procesando..." : "Importar"}
          </button>
        </form>
        <p style={{ fontSize: 13, color: "#8a8a8a" }}>
          Formatos aceptados: planilla simple (Empleado, Hora de entrada, Hora de salida) o reporte ZKTeco StandardReport (.xls). Los empleados nuevos se crean automáticamente.
        </p>
      </div>

      <div className="card">
        <h2><Icon name="chart" size={20} /> Distribución de asistencia</h2>
        {chart ? (
          <Donut present={chart.present} absent={chart.absent} late={chart.late} />
        ) : (
          <p style={{ color: "#8a8a8a" }}>Cargando gráfica...</p>
        )}
      </div>

      <div className="card">
        <h2><Icon name="search" size={20} /> Registros y QR del reporte</h2>
        <div className="toolbar">
          <div className="field">
            <label>Empleado</label>
            <select className="input" value={filters.employee_id} onChange={(e) => setFilters({ ...filters, employee_id: e.target.value })}>
              <option value="">Todos</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>{emp.name}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Desde</label>
            <input className="input" type="date" value={filters.start_date} onChange={(e) => setFilters({ ...filters, start_date: e.target.value })} />
          </div>
          <div className="field">
            <label>Hasta</label>
            <input className="input" type="date" value={filters.end_date} onChange={(e) => setFilters({ ...filters, end_date: e.target.value })} />
          </div>
          <div className="field">
            <label>Departamento</label>
            <select className="input" value={filters.department} onChange={(e) => setFilters({ ...filters, department: e.target.value })}>
              <option value="">Todos</option>
              {departments.map((d) => (
                <option key={d.id} value={d.name}>{d.name}</option>
              ))}
            </select>
          </div>
          <button className="btn btn-ghost" onClick={loadAll}>Filtrar</button>
          <button className="btn btn-gold" onClick={handleQR} disabled={loading}><Icon name="qr" size={16} /> QR del reporte</button>
          <button className="btn btn-ghost" onClick={handleDocx} disabled={loading}><Icon name="download" size={16} /> Descargar Word</button>
        </div>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr><th>Empleado</th><th>Fecha</th><th>Entrada</th><th>Salida</th><th>Horas</th><th>Origen</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const emp = employees.find((e) => e.id === r.employee_id);
                return (
                  <tr key={r.id}>
                    <td>{emp ? emp.name : "#" + r.employee_id}</td>
                    <td>{r.date}</td>
                    <td>{r.check_in || "-"}</td>
                    <td>{r.check_out || "-"}</td>
                    <td>{r.total_hours || "-"}</td>
                    <td><span className="badge badge-gold">{r.source}</span></td>
                  </tr>
                );
              })}
              {rows.length === 0 && (
                <tr><td colSpan="6" style={{ color: "#8a8a8a" }}>Sin registros. Importa el Excel del ponchador para comenzar.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h2><Icon name="memo" size={20} /> Justificaciones por rango de fechas</h2>
        <form onSubmit={handleJustify}>
          <div className="form-grid">
            <div className="field">
              <label>Empleado</label>
              <select className="input" required value={justForm.employee_id}
                onChange={(e) => { setJustForm({ ...justForm, employee_id: e.target.value }); loadJustifs(e.target.value); }}>
                <option value="">Seleccionar...</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>{emp.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Tipo</label>
              <select className="input" value={justForm.type} onChange={(e) => setJustForm({ ...justForm, type: e.target.value })}>
                <option value="permiso">Permiso</option>
                <option value="licencia_medica">Licencia médica</option>
                <option value="vacaciones">Vacaciones</option>
                <option value="otro">Otro</option>
              </select>
            </div>
            <div className="field">
              <label>Desde</label>
              <input className="input" type="date" required value={justForm.start_date} onChange={(e) => setJustForm({ ...justForm, start_date: e.target.value })} />
            </div>
            <div className="field">
              <label>Hasta</label>
              <input className="input" type="date" required value={justForm.end_date} onChange={(e) => setJustForm({ ...justForm, end_date: e.target.value })} />
            </div>
          </div>
          <div className="form-grid">
            <div className="field" style={{ gridColumn: "1 / -1" }}>
              <label>Descripción</label>
              <input className="input" value={justForm.description} onChange={(e) => setJustForm({ ...justForm, description: e.target.value })} placeholder="Motivo de la justificación" />
            </div>
          </div>
          <button className="btn btn-gold">Guardar justificación</button>
        </form>
        {justifs.length > 0 && (
          <div className="table-wrap" style={{ marginTop: 18 }}>
            <table className="data">
              <thead><tr><th>Tipo</th><th>Desde</th><th>Hasta</th><th>Estado</th></tr></thead>
              <tbody>
                {justifs.map((j) => (
                  <tr key={j.id}>
                    <td>{j.type}</td><td>{j.start_date}</td><td>{j.end_date}</td>
                    <td>{j.is_active ? <span className="badge badge-green">Vigente</span> : <span className="badge badge-gray">Anulada</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card">
        <h2><Icon name="users" size={20} /> Empleados</h2>
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Nombre</th><th>Departamento</th><th>Estado</th><th>Acciones</th></tr></thead>
            <tbody>
              {employees.map((emp) => (
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
                      <input className="input" value={empForm.department} list="dept-list"
                        onChange={(e) => setEmpForm({ ...empForm, department: e.target.value })} placeholder="Departamento" />
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
              {employees.length === 0 && (
                <tr><td colSpan="4" style={{ color: "#8a8a8a" }}>Sin empleados. Importa el Excel del ponchador para comenzar.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <datalist id="dept-list">
          {departments.map((d) => (
            <option key={d.id} value={d.name} />
          ))}
        </datalist>
      </div>

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

      {qr && (
        <div className="modal-back" onClick={() => setQr(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2><Icon name="qr" size={20} /> Escanea para ver el reporte</h2>
            <img className="qr" src={"data:image/png;base64," + qr.qr_base64} alt="QR del reporte" />
            <p className="url">{qr.url}</p>
            <button className="btn btn-gold" onClick={() => setQr(null)}>Cerrar</button>
          </div>
        </div>
      )}
    </Layout>
  );
}
