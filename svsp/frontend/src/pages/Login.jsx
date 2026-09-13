import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError("Correo o contraseña incorrectos.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ios-login-screen">
      <form className="ios-login-card" onSubmit={handleSubmit}>
        <h1 className="ios-page-title" style={{ marginBottom: 4 }}>
          SVSP
        </h1>
        <p style={{ color: "var(--ios-secondary-label)", marginTop: 0, marginBottom: 24 }}>
          Sistema de Asistencia y Visitas
        </p>

        <label className="ios-label" style={{ textAlign: "left" }}>
          Correo
        </label>
        <input
          className="ios-input"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label className="ios-label" style={{ textAlign: "left" }}>
          Contraseña
        </label>
        <input
          className="ios-input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {error && <p className="ios-error-text">{error}</p>}

        <button className="ios-btn ios-btn--primary" style={{ width: "100%" }} disabled={loading}>
          {loading ? "Ingresando..." : "Ingresar"}
        </button>
      </form>
    </div>
  );
}
