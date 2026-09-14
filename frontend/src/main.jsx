import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider, Navigate, useNavigate } from 'react-router-dom'

const API = 'http://localhost:8000'

function useAuth() {
  const token = localStorage.getItem('user_token')
  const modules = JSON.parse(localStorage.getItem('user_modules') || '[]')
  return { token, modules }
}

function LoginRedirect() {
  useEffect(() => {
    window.location.href = '/login.html'
  }, [])
  return <p style={{ padding: 40, fontFamily: 'sans-serif' }}>Redirigiendo al inicio de sesión...</p>
}

function Protected({ children }) {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return children
}

function Dashboard() {
  const navigate = useNavigate()
  const { modules } = useAuth()
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(API + '/api/v1/attendance/stats', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('user_token') },
    })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status)
        return r.json()
      })
      .then(setStats)
      .catch(function (e) { setError('No se pudieron cargar las estadísticas.') })
  }, [])

  function logout() {
    localStorage.removeItem('user_token')
    localStorage.removeItem('user_modules')
    navigate('/login')
  }

  const cards = stats
    ? [
        { label: 'Total Empleados', value: stats.total_employees },
        { label: 'Presentes', value: stats.present_today },
        { label: 'Ausentes', value: stats.absent_today },
        { label: 'Tardanzas', value: stats.late_today },
        { label: 'Horas totales', value: stats.total_hours },
      ]
    : []

  return (
    <div style={{ fontFamily: 'sans-serif', background: '#faf8f3', minHeight: '100vh', padding: 32 }}>
      <div style={{ maxWidth: 1000, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 32, color: '#2c2c2c' }}>SVSP - Panel Principal</h1>
            <p style={{ color: '#8a8a8a', marginTop: 6 }}>Módulos asignados: {(modules || []).join(', ') || 'ninguno'}</p>
          </div>
          <button onClick={logout} style={{ padding: '12px 24px', borderRadius: 10, border: '1px solid #e8e0d0', background: '#fff', cursor: 'pointer', fontSize: 15, fontWeight: 600 }}>Salir</button>
        </div>
        {error && <p style={{ background: '#fff0f0', border: '1px solid #fecaca', color: '#b91c1c', padding: 14, borderRadius: 12, marginBottom: 20 }}>{error}</p>}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
          {cards.map(function (c) {
            return (
              <div key={c.label} style={{ background: '#fff', border: '1px solid #f0e6cf', borderRadius: 16, padding: 24, boxShadow: '0 8px 20px rgba(180,140,40,0.10)' }}>
                <div style={{ color: '#8a8a8a', fontSize: 14, marginBottom: 8 }}>{c.label}</div>
                <div style={{ fontSize: 34, fontWeight: 800, color: '#B8912F' }}>{c.value}</div>
              </div>
            )
          })}
        </div>
        {!stats && !error && <p style={{ marginTop: 24, color: '#8a8a8a' }}>Cargando estadísticas...</p>}
      </div>
    </div>
  )
}

const router = createBrowserRouter([
  { path: '/login', element: <LoginRedirect /> },
  { path: '/', element: <Navigate to="/login" replace /> },
  { path: '/dashboard', element: <Protected><Dashboard /></Protected> },
  { path: '*', element: <Navigate to="/login" replace /> },
])

ReactDOM.createRoot(document.getElementById('root')).render(<RouterProvider router={router} />)
