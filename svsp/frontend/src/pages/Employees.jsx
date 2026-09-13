import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import apiClient from "../api/client";
import { Layout } from "../components/Layout";

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [fullName, setFullName] = useState("");
  const [department, setDepartment] = useState("");
  const [importSummary, setImportSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  async function loadEmployees() {
    const res = await apiClient.get("/api/employees/");
    setEmployees(res.data);
  }

  useEffect(() => {
    loadEmployees();
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    await apiClient.post("/api/employees/", { full_name: fullName, department });
    setFullName("");
    setDepartment("");
    loadEmployees();
  }

  async function handleToggle(employee) {
    const action = employee.status === "active" ? "disable" : "enable";
    await apiClient.post(`/api/employees/${employee.id}/${action}`);
    loadEmployees();
  }

  async function handleImport(e) {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    try {
      const res = await apiClient.post("/api/attendance/import", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setImportSummary(res.data);
      loadEmployees();
    } finally {
      setLoading(false);
      e.target.value = "";
    }
  }

  const departmentChartData = Object.values(
    employees.reduce((acc, emp) => {
      acc[emp.department] = acc[emp.department] || { department: emp.department, count: 0 };
      acc[emp.department].count += 1;
      return acc;
    }, {})
  );

  return (
    <Layout title="Asistencia">
      <h1 className="ios-page-title">Empleados</h1>

      <p className="ios-list-group__title">Cargar reporte del poncher</p>
      <div className="ios-card" style={{ padding: 16 }}>
        <input type="file" accept=".xlsx,.xls" onChange={handleImport} disabled={loading} />
        {loading && <p className="ios-list-row__meta">Procesando archivo...</p>}
        {importSummary && (
          <p className="ios-list-row__meta">
            {importSummary.attendances_created} registros procesados, {importSummary.employees_created} empleados
            nuevos.
          </p>
        )}
      </div>

      <p className="ios-list-group__title">Empleados por departamento</p>
      <div className="ios-card" style={{ padding: 16, height: 220 }}>
        {departmentChartData.length === 0 ? (
          <p className="ios-empty-state">Aún no hay empleados registrados.</p>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={departmentChartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="department" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#007aff" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <p className="ios-list-group__title">Agregar empleado manualmente</p>
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
          placeholder="Departamento"
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          required
        />
        <button className="ios-btn ios-btn--primary" style={{ width: "100%" }}>
          Agregar
        </button>
      </form>

      <p className="ios-list-group__title">Listado</p>
      <div className="ios-card">
        {employees.length === 0 && <p className="ios-empty-state">No hay empleados todavía.</p>}
        {employees.map((emp) => (
          <div className="ios-list-row" key={emp.id}>
            <div>
              <div>{emp.full_name}</div>
              <div className="ios-list-row__meta">{emp.department}</div>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span className={`ios-badge ${emp.status === "active" ? "ios-badge--green" : "ios-badge--red"}`}>
                {emp.status === "active" ? "Activo" : "Inhabilitado"}
              </span>
              <button
                className={`ios-btn ios-btn--sm ${emp.status === "active" ? "ios-btn--danger" : "ios-btn--secondary"}`}
                onClick={() => handleToggle(emp)}
              >
                {emp.status === "active" ? "Inhabilitar" : "Rehabilitar"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </Layout>
  );
}
