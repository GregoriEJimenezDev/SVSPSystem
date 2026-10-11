import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import { api } from "../services/api";
import Icon from "../components/icons";

function downloadQR(qrBase64, name) {
  const link = document.createElement("a");
  link.href = `data:image/png;base64,${qrBase64}`;
  link.download = `QR_${name.replace(/\s+/g, "_")}.png`;
  link.click();
}

export default function Visitas() {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState({ first_name: "", last_name: "", document_number: "", visited_person: "", institution: "", visit_justification: "" });
  const [search, setSearch] = useState("");
  const [msg, setMsg] = useState({ type: "", text: "" });
  const [qr, setQr] = useState(null);
  const [loading, setLoading] = useState(false);

  function load() {
    api
      .get("/api/v1/visitors/")
      .then(setRows)
      .catch((e) => setMsg({ type: "error", text: e.message }));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleRegister(e) {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await api.post("/api/v1/visitors/", form);
      setQr({ ...r, url: null });
      setMsg({ type: "ok", text: `Visitante ${r.visitor.first_name} ${r.visitor.last_name} registrado.` });
      setForm({ first_name: "", last_name: "", document_number: "", visited_person: "", institution: "", visit_justification: "" });
      load();
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
    setLoading(false);
  }

async function handleDownloadQR(v) {
  try {
    const r = await api.get(`/api/v1/visitors/${v.id}/qr`);
    downloadQR(r.qr_base64, `${r.visitor.first_name} ${r.visitor.last_name}`);
  } catch (err) {
    setMsg({ type: "error", text: err.message });
  }
}

async function handleQR(id) {
  try {
    const r = await api.get(`/api/v1/visitors/${id}/qr`);
    setQr(r);
  } catch (err) {
    setMsg({ type: "error", text: err.message });
  }
}

  async function handleVerify(id) {
    try {
      await api.post(`/api/v1/visitors/${id}/verify`);
      setMsg({ type: "ok", text: "Visitante verificado." });
      load();
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
  }

  const filtered = rows.filter((v) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      (v.first_name + " " + v.last_name).toLowerCase().includes(q) ||
      v.document_number.toLowerCase().includes(q)
    );
  });

  return (
    <Layout title="Módulo de Visitas" desc="Registra visitantes, genera su QR y verifica identidad al escanear.">
      {msg.text && <div className={`alert alert-${msg.type === "ok" ? "ok" : "error"}`}>{msg.text}</div>}

      <div className="card">
        <h2><Icon name="plus" size={20} /> Registrar visitante</h2>
        <form onSubmit={handleRegister}>
          <div className="form-grid">
            <div className="field">
              <label>Nombre</label>
              <input className="input" required value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} placeholder="Nombre" />
            </div>
            <div className="field">
              <label>Apellido</label>
              <input className="input" required value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} placeholder="Apellido" />
            </div>
            <div className="field">
              <label>Cédula</label>
              <input className="input" required value={form.document_number} onChange={(e) => setForm({ ...form, document_number: e.target.value })} placeholder="Número de cédula" />
            </div>
            <div className="field">
              <label>¿A quién visita?</label>
              <input className="input" value={form.visited_person} onChange={(e) => setForm({ ...form, visited_person: e.target.value })} placeholder="Persona visitada" />
            </div>
            <div className="field">
              <label>Institución de origen</label>
              <input className="input" value={form.institution} onChange={(e) => setForm({ ...form, institution: e.target.value })} placeholder="¿De qué institución viene?" />
            </div>
            <div className="field" style={{ gridColumn: "1 / -1" }}>
              <label>Justificación de la visita</label>
              <input className="input" value={form.visit_justification} onChange={(e) => setForm({ ...form, visit_justification: e.target.value })} placeholder="Motivo de la visita" />
            </div>
          </div>
          <button className="btn btn-gold" disabled={loading}>
            {loading ? "Registrando..." : "Registrar y generar QR"}
          </button>
        </form>
      </div>

      <div className="card">
        <h2><Icon name="clipboard" size={20} /> Historial de visitantes</h2>
        <div className="toolbar">
          <div className="field" style={{ minWidth: 240 }}>
            <label>Buscar por nombre o cédula</label>
            <input className="input" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar..." />
          </div>
        </div>
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Nombre</th><th>Cédula</th><th>Visita a</th><th>Estado</th><th>Acciones</th></tr></thead>
            <tbody>
              {filtered.map((v) => (
                <tr key={v.id}>
                  <td>{v.first_name} {v.last_name}</td>
                  <td>{v.document_number}</td>
                  <td>{v.visited_person || "—"}{v.institution ? ` (${v.institution})` : ""}</td>
                  <td>
                    {v.is_verified
                      ? <span className="badge badge-green">Verificado</span>
                      : <span className="badge badge-gold">Registrado</span>}
                  </td>
                  <td style={{ display: "flex", gap: 8 }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleQR(v.id)}>QR</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleDownloadQR(v)}>Descargar</button>
                    {!v.is_verified && (
                      <button className="btn btn-gold btn-sm" onClick={() => handleVerify(v.id)}>Verificar</button>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan="5" style={{ color: "#8a8a8a" }}>Sin visitantes registrados.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {qr && (
        <div className="modal-back" onClick={() => setQr(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2><Icon name="qr" size={20} /> QR del visitante</h2>
            <p style={{ color: "#8a8a8a", marginTop: 8 }}>
              {qr.visitor.first_name} {qr.visitor.last_name} · {qr.visitor.document_number}
            </p>
            <img className="qr" src={"data:image/png;base64," + qr.qr_base64} alt="QR del visitante" />
            <button className="btn btn-gold" style={{ marginTop: 12 }}
              onClick={() => downloadQR(qr.qr_base64, `${qr.visitor.first_name} ${qr.visitor.last_name}`)}>
              <Icon name="download" size={16} /> Descargar QR
            </button>
            <p style={{ fontSize: 13, color: "#8a8a8a" }}>Al escanear se muestra la ficha sin necesidad de login.</p>
            <button className="btn btn-ghost" onClick={() => setQr(null)} style={{ marginTop: 12 }}>Cerrar</button>
          </div>
        </div>
      )}
    </Layout>
  );
}
