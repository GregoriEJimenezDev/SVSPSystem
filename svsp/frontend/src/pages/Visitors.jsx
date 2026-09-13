import { useEffect, useState } from "react";
import apiClient from "../api/client";
import { Layout } from "../components/Layout";

export default function Visitors() {
  const [visitors, setVisitors] = useState([]);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [cedula, setCedula] = useState("");
  const [lastQr, setLastQr] = useState(null);
  const [search, setSearch] = useState("");

  async function loadVisitors(query = "") {
    const res = await apiClient.get("/api/visitors/", { params: query ? { q: query } : {} });
    setVisitors(res.data);
  }

  useEffect(() => {
    loadVisitors();
  }, []);

  async function handleRegister(e) {
    e.preventDefault();
    const res = await apiClient.post("/api/visitors/", {
      first_name: firstName,
      last_name: lastName,
      cedula,
    });
    setLastQr(res.data.qr_code_base64);
    setFirstName("");
    setLastName("");
    setCedula("");
    loadVisitors();
  }

  async function handleVerify(id) {
    await apiClient.post(`/api/visitors/${id}/verify`);
    loadVisitors();
  }

  function handleSearch(e) {
    e.preventDefault();
    loadVisitors(search);
  }

  return (
    <Layout title="Visitas">
      <h1 className="ios-page-title">Visitantes</h1>

      <p className="ios-list-group__title">Registrar visitante</p>
      <form className="ios-card" style={{ padding: 16 }} onSubmit={handleRegister}>
        <input
          className="ios-input"
          placeholder="Nombre"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          required
        />
        <input
          className="ios-input"
          placeholder="Apellido"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          required
        />
        <input
          className="ios-input"
          placeholder="Cédula"
          value={cedula}
          onChange={(e) => setCedula(e.target.value)}
          required
        />
        <button className="ios-btn ios-btn--primary" style={{ width: "100%" }}>
          Registrar y generar QR
        </button>
      </form>

      {lastQr && (
        <div className="ios-card" style={{ padding: 20, textAlign: "center" }}>
          <p className="ios-list-row__meta" style={{ marginBottom: 12 }}>
            Código QR del último visitante registrado
          </p>
          <img
            src={`data:image/png;base64,${lastQr}`}
            alt="Código QR del visitante"
            style={{ width: 180, height: 180 }}
          />
        </div>
      )}

      <p className="ios-list-group__title">Buscar por nombre o cédula</p>
      <form className="ios-card" style={{ padding: 16, display: "flex", gap: 8 }} onSubmit={handleSearch}>
        <input
          className="ios-input"
          style={{ marginBottom: 0 }}
          placeholder="Buscar..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button className="ios-btn ios-btn--secondary">Buscar</button>
      </form>

      <p className="ios-list-group__title">Historial</p>
      <div className="ios-card">
        {visitors.length === 0 && <p className="ios-empty-state">No hay visitantes registrados.</p>}
        {visitors.map((v) => (
          <div className="ios-list-row" key={v.id}>
            <div>
              <div>
                {v.first_name} {v.last_name}
              </div>
              <div className="ios-list-row__meta">Cédula: {v.cedula}</div>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span className={`ios-badge ${v.status === "verified" ? "ios-badge--green" : "ios-badge--red"}`}>
                {v.status === "verified" ? "Verificado" : "Registrado"}
              </span>
              {v.status !== "verified" && (
                <button className="ios-btn ios-btn--sm ios-btn--secondary" onClick={() => handleVerify(v.id)}>
                  Verificar
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </Layout>
  );
}
