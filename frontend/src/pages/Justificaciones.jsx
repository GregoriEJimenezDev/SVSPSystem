import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import Icon from "../components/icons";
import { api } from "../services/api";

export default function Justificaciones() {
  const [employees, setEmployees] = useState([]);
  const [justifs, setJustifs] = useState([]);
  const [justForm, setJustForm] = useState({ employee_id: "", type: "permiso", description: "", start_date: "", end_date: "" });
  const [msg, setMsg] = useState({ type: "", text: "" });

  useEffect(() => {
    api
      .get("/api/v1/employees/")
      .then(setEmployees)
      .catch((e) => setMsg({ type: "error", text: e.message }));
  }, []);

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

  return (
    <Layout title="Justificaciones" desc="Registra permisos, licencias y vacaciones por empleado.">
      {msg.text && <div className={`alert alert-${msg.type === "ok" ? "ok" : "error"}`}>{msg.text}</div>}

      <div className="card">
        <h2><Icon name="memo" size={20} /> Registrar justificación</h2>
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
    </Layout>
  );
}
