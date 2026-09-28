import { useState, useEffect } from "react"
import "./index.css"

const AttendanceSystem = () => {
  const [attendees, setAttendees] = useState([])
  const [newName, setNewName] = useState("")
  const [searchTerm, setSearchTerm] = useState("")
  const [importResult, setImportResult] = useState(null)
  const [dashboard, setDashboard] = useState({
    presentes: 0,
    ausentes: 0,
    tardanzas: 0,
    porDepartamento: []
  })
  const [empleados, setEmpleados] = useState([])

  useEffect(() => {
    const saved = localStorage.getItem("attendanceData")
    if (saved) {
      const data = JSON.parse(saved)
      setAttendees(data.attendees || [])
      setDashboard(data.dashboard || {
        presentes: 0, ausentes: 0, tardanzas: 0, porDepartamento: []
      })
      setEmpleados(data.empleados || [])
    }
  }, [])

  useEffect(() => {
    localStorage.setItem(
      "attendanceData",
      JSON.stringify({
        attendees: attendees,
        dashboard: dashboard,
        empleados: empleados
      })
    )
  }, [attendees, dashboard, empleados])

  const addAttendee = () => {
    if (newName.trim()) {
      setAttendees([
        ...attendees,
        {
          id: Date.now(),
          name: newName,
          status: "present",
          time: new Date().toLocaleTimeString(),
          departamento: ""
        }
      ])
      setNewName("")
    }
  }

  const removeAttendee = (id) => {
    setAttendees(attendees.filter((a) => a.id !== id))
  }

  const toggleStatus = (id) => {
    setAttendees(
      attendees.map((a) =>
        a.id === id
          ? { ...a, status: a.status === "present" ? "absent" : "present" }
          : a
      )
    )
  }

  const filteredAttendees = attendees.filter((a) =>
    a.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const importExcel = (e) => {
    const file = e.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: "array" })
      const firstSheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[firstSheetName]
      const json = XLSX.utils.sheet_to_json(worksheet)

      const nuevoEmpleado = {
        nombre: json[0]?.["Nombre"] || "",
        departamento: json[0]?.["Departamento"] || ""
      }

      let empleadosCreados = 0
      let duplicados = 0
      const registros = []

      json.forEach((row, index) => {
        const nombre = row["Nombre"] || ""
        const depto = row["Departamento"] || ""
        const fechaHora = row["Fecha Hora"] || row["Fecha"] || row["Hora"]

        if (!nombre) return

        let emp = empleados.find((e) => e.nombre === nombre)
        if (!emp) {
          emp = {
            id: Date.now() + index,
            nombre,
            departamento: depto
          }
          setEmpleados([...empleados, emp])
          empleadosCreados++
        } else {
          emp.departamento = depto
          duplicados++
        }

        const existe = attendees.some(
          (a) => a.nombre === nombre && a.departamento === depto
        )
        if (!existe) {
          registros.push({
            id: Date.now() + index * 1000,
            nombre,
            departamento: depto,
            status: "present",
            time: fechaHora || new Date().toLocaleTimeString()
          })
        }
      })

      setAttendees([
        ...attendees,
        ...registros.filter(
          (r) =>
            attendees.every(
              (a) => a.nombre !== r.nombre || a.departamento !== r.departamento
            )
        )
      ])
      setImportResult({ empleadosCreados, duplicados, total: json.length })

      // Actualizar dashboard
      const calculo = calcularDashboard(attendees)
      setDashboard(calculo)
    }
    reader.readAsArrayBuffer(file)
  }

  const calcularDashboard = (data) => {
    let presentes = 0
    let ausentes = 0
    let tardanzas = 0
    const mapaDepto = {}

    data.forEach((a) => {
      if (a.status === "present") presentes++
      else ausentes++

      const d = a.departamento || "Sin Depto"
      mapaDepto[d] = (mapaDepto[d] || 0) + 1
    })

    const porDepartamento = Object.entries(mapaDepto).map(
      ([nombre, count]) => ({
        nombre,
        count,
        presentes: 0,
        tardanzas: 0
      })
    )

    return { presentes, ausentes, tardanzas: 0, porDepartamento }
  }

  return (
    <div className="min-h-screen bg-ios-background text-ios-text font-sans">
      <nav className="ios-navbar text-ios-text">
        <div className="max-w-7xl mx-auto flex items-center justify-between h-full">
          <h1 className="text-xl font-medium">SVSP - Sistema</h1>
          <div className="hidden md:flex items-center gap-4">
            <span className="text-ios-text-secondary text-xs">Bienvenido</span>
          </div>
        </div>
      </nav>

      <main className="p-4 md:p-6 max-w-7xl mx-auto">
        {/* Dashboard Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
          <div className="ios-card">
            <div className="text-primary-600 text-2xl font-bold">{dashboard.presentes}</div>
            <p className="text-ios-text-secondary text-sm m-0">Presente</p>
          </div>
          <div className="ios-card bg-red-50�">
            <div className="text-red-600 text-2xl font-bold">{dashboard.ausentes}</div>
            <p className="text-ios-text-secondary text-sm m-0">Ausente</p>
          </div>
          <div className="ios-card text-yellow-600">
            <div className="text-yellow-600 text-2xl font-bold">{dashboard.tardanzas}</div>
            <p className="text-ios-text-secondary text-sm m-0">Tardanzas</p>
          </div>
          <div className="ios-card text-blue-600">
            <div className="text-blue-600 text-2xl font-bold">{empleados.length}</div>
            <p className="text-ios-text-secondary text-sm m-0">Empleados</p>
          </div>
        </div>

        {/* Attendance Table */}
        <div className="ios-card mb-6">
          <div className="p-4 border-b border-ios-divider">
            <h2 className="font-medium text-lg">Historial de Asistentes</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full ios-table">
              <thead>
                <tr className="text-ios-text-secondary text-xs border-b border-ios-divider">
                  <th className="p-3">#</th>
                  <th className="p-3">Nombre</th>
                  <th className="p-3">Departamento</th>
                  <th className="p-3">Estado</th>
                  <th className="p-3">Hora Entrada</th>
                  <th className="p-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filteredAttendees.map((attendee) => (
                  <tr key={attendee.id} className="ios-table-row">
                    <td className="p-3 text-ios-text-secondary text-sm">{attendee.id}</td>
                    <td className="p-3 text-ios-text font-medium">{attendee.name}</td>
                    <td className="p-3 text-ios-text-secondary text-sm">
                      {attendee.departamento || "---"}
                    </td>
                    <td className="p-3">
                      <span
                        className={
                          attendee.status === "present"
                            ? "ios-badge ios-badge-success"
                            : "ios-badge ios-badge-error"
                        }
                      >
                        {attendee.status}
                      </span>
                    </td>
                    <td className="p-3 text-ios-text-secondary text-sm">{attendee.time}</td>
                    <td className="p-3 text-right">
                      <div className="btn-group btn-group-sm">
                        <button
                          onClick={() => toggleStatus(attendee.id)}
                          className={`btn btn-pill ${attendee.status === "present" ? "ios-btn-pill" : "ios-btn-pill ios-btn-pill-outline"}}>
                          <small>
                            {attendee.status === "present" ? "Ausente" : "Presente"}
                          </small>
                        </button>
                        <button
                          onClick={() => removeAttendee(attendee.id)}
                          className="btn btn-danger text-sm">
                          <small>Quitar</small>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Search filter */}
        <div className="ios-card mb-6">
          <div className="p-4 border-b border-ios-divider">
            <h2 className="font-medium text-lg">Buscar Asistente</h2>
          </div>
          <div className="p-4">
            <div className="row">
              <div className="col-md-6 mb-3">
                <div className="form-group">
                  <input
                    type="text"
                    className="ios-input"
                    placeholder="Buscar por nombre..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
              <div className="col-md-6 mb-3">
                <div className="form-group">
                  <button
                    type="button"
                    className="btn btn-primary btn-block ios-btn-pill"
                    onClick={() => setSearchTerm("")}
                  >
                    Limpiar Filtro
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Import Excel Section */}
        <div className="ios-card mb-6">
          <div className="p-4 border-b border-ios-divider">
            <h2 className="font-medium text-lg">Importar Planilla Pouncher (Excel)</h2>
          </div>
          <div className="p-4">
            <p className="text-ios-text-secondary text-sm mb-3">
              Formato fijo: Columna A = Nombre, Columna B = Departamento, Columna C = Fecha/Hora
            </p>
            <form>
              <div className="row">
                <div className="col-md-6 mb-3">
                  <div className="form-group">
                    <input
                      type="file"
                      className="ios-input"
                      accept=".xlsx, .xls"
                      onChange={importExcel}
                    />
                  </div>
                </div>
                <div className="col-md-6 mb-3">
                  <div className="form-group">
                    <button
                      type="button"
                      className="btn btn-primary btn-block ios-btn-pill"
                      onClick={() => setImportResult(null)}
                      disabled={!importResult}
                    >
                      Limpiar Resultados
                    </button>
                  </div>
                </div>
              </div>
            </form>
            {importResult && (
              <div className="mt-4 p-3 bg-ios-surface rounded">
                <h3 className="mb-2 text-ios-text-semibold">Resultados de Importación</h3>
                <div className="row">
                  <div className="col-4">
                    <small className="text-ios-primary">Empleados Creados:</small> {importResult.empleadosCreados}
                  </div>
                  <div className="col-4">
                    <small className="text-ios-warning">Duplicados (actualizados):</small> {importResult.duplicados}
                  </div>
                  <div className="col-4">
                    <small>Total Filas:</small> {importResult.total}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

function App() {
  return (
    <div>
      <AttendanceSystem />
    </div>
  )
}

export default App