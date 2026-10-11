# Especificación de Requerimientos de Software (SRS) — SVSP System

**Sistema Web de Gestión de Asistencia y Visitas — SVSP**
Versión del documento: 1.0 · Fecha: octubre 2026 · Estado: vigente (`main`)

---

## 1. Introducción

### 1.1 Propósito
Definir qué hace el sistema SVSP, quién lo usa y bajo qué reglas opera,
para alinear desarrollo, operación y auditoría.

### 1.2 Alcance
Sistema web con backend FastAPI (Python) y frontend React/Vite. Cubre:
control de asistencia por ponchador biométrico, gestión de empleados y
departamentos, justificaciones, registro y verificación de visitantes
(con QR y PDF), administración de usuarios (AdminPRO) y bitácora de
auditoría. Base de datos PostgreSQL (Neon) en producción.

### 1.3 Definiciones
- **Ponchador**: reloj biométrico que genera los reportes de asistencia.
- **ZKTeco StandardReport**: formato `.xls` del ponchador con hojas por
  estadística, registros y tarjetas.
- **AdminPRO**: rol con acceso total (usuarios, auditoría, estadísticas).
- **Baja lógica**: inhabilitar (`is_active=false`) sin borrar filas.

---

## 2. Descripción general

### 2.1 Usuarios y roles (módulos)
| Rol / módulo | Acceso |
|---|---|
| `asistencia` | Asistencia, Empleados, Justificaciones, Departamentos |
| `visitas` | Registro/verificación de visitantes |
| `adminpro` | Todo lo anterior + usuarios, auditoría, estadísticas |

### 2.2 Supuestos
- Los reportes del ponchador llegan en `.xls` (ZKTeco) o `.xlsx` simple.
- Un empleado se identifica por su **nombre normalizado** (sin espacios
  extra, insensible a mayúsculas).
- La hora límite de llegada es **08:00** (tardanza si la entrada es posterior).

---

## 3. Requerimientos funcionales

### RF-01 Autenticación
- RF-01.1 Registro con email + nombre + clave (mín. 8) + módulos.
- RF-01.2 Login devuelve `access_token` (JWT Bearer) + datos del usuario.
- RF-01.3 Clave errónea o usuario inexistente → **401 "Credenciales incorrectas"**
  (nunca error de conexión por este motivo).
- RF-01.4 `GET /api/v1/auth/me` devuelve el perfil del token vigente.

### RF-02 Empleados
- RF-02.1 **Auto-creación al importar Excel** (nombres normalizados; actualiza
  el departamento si cambió). No duplica por espacios/capitalización.
- RF-02.2 Crear, editar (nombre, departamento) e inhabilitar/rehabilitar.
- RF-02.3 Filtrar por departamento (coincidencia parcial).
- RF-02.4 **Detección de duplicados** (`GET /employees/duplicates`: mismo
  nombre normalizado) y **fusión** (`POST /employees/merge`): mueve
  asistencias/justificaciones al conservado e inhabilita el resto (nada se borra).

### RF-03 Departamentos
- RF-03.1 CRUD: crear, renombrar, inhabilitar/rehabilitar (baja lógica).
- RF-03.2 No duplica (insensible a mayúsculas/espacios); no se puede
  inhabilitar si tiene empleados activos.
- RF-03.3 **Se crean solos** con los departamentos vistos en cada import
  (idempotente; el resultado informa `departments_created`).

### RF-04 Asistencia (importación)
- RF-04.1 Acepta **`.xls` y `.xlsx`**.
- RF-04.2 Planilla simple: columnas `Empleado`, `Hora_entrada`, `Hora_salida`
  (por encabezado, en cualquier orden).
- RF-04.3 ZKTeco StandardReport: detecta la hoja de registros por día
  (`Name`, `Department`, `Date`, `On-duty`, `Off-duty`); cada fila crea o
  actualiza la asistencia **en su fecha** y actualiza el departamento.
- RF-04.4 **Se omiten filas sin marcaciones** (ni entrada ni salida): no crean
  empleado ni registro; se cuentan en `skipped` y se informan en el mensaje.
- RF-04.5 Respuesta: `processed`, `created`, `updated`, `skipped`,
  `departments_created`, `errors` (máx. 50).

### RF-05 Estadísticas coherentes
- RF-05.1 Día de referencia = fin del rango filtrado, o inicio, u hoy.
- RF-05.2 **Presentes** = empleados distintos con entrada ese día
  (**nunca** supera el total de empleados).
- RF-05.3 **Ausentes** = empleados activos − presentes (mínimo 0).
- RF-05.4 **Tardanzas** = entradas posteriores a las 08:00.
- RF-05.5 Respeta filtros de empleado, departamento y fechas (aplica a
  `/stats`, `/chart-data`, listados y reportes).

### RF-06 Reportes
- RF-06.1 **QR del reporte** (`POST /report-qr`): enlace firmando filtros,
  válido 7 días, ficha HTML pública sin login.
- RF-06.2 **Word editable** (`POST /report-docx`, mismos filtros): `.docx`
  con tabla Empleado | Hora de entrada | Hora salida | Total horas
  trabajadas + encabezado (período, departamento, fecha, total).
  Se genera **en memoria y se descarga**; no se guarda en el servidor.

### RF-07 Justificaciones
- RF-07.1 Registrar por empleado: tipo (`permiso`, `licencia_medica`,
  `vacaciones`, `otro`), descripción, rango de fechas.
- RF-07.2 Listar por empleado y anular (baja lógica).

### RF-08 Visitas
- RF-08.1 Registrar con nombre, apellido, cédula, **persona visitada**,
  **institución de origen** y **justificación**; genera QR de verificación.
- RF-08.2 Re-registro por cédula actualiza la visita (no duplica).
- RF-08.3 Verificar al escanear; ficha pública HTML sin login (muestra
  persona visitada e institución; la justificación no es pública).
- RF-08.4 **Ficha PDF descargable** (`GET /visitors/{id}/pdf`): QR + nombre,
  cédula, institución, persona visitada, justificación, estado y fecha.

### RF-09 AdminPRO
- RF-09.1 Crear/listar/editar/inhabilitar usuarios (no se puede inhabilitar
  al último administrador).
- RF-09.2 **Cambiar la contraseña de cualquier usuario**
  (`PUT /adminpro/users/{id}/password`, mín. 8). La clave nunca se devuelve
  ni se registra en logs; el cambio queda auditado.
- RF-09.3 Bitácora (`GET /adminpro/audit-log`) y estadísticas del sistema.

---

## 4. Requerimientos no funcionales

- **RNF-01 Seguridad**: JWT HS256, bcrypt, CORS restringido (+ regex para
  `*.app.github.dev` en desarrollo), credenciales solo por variables de
  entorno (`.env` gitignorado + `gitleaks` en pre-commit). Prohibido
  hardcodear secretos.
- **RNF-02 Auditoría**: toda acción relevante (usuarios, importaciones,
  visitas, reportes, fusiones, cambios de clave) deja registro con actor,
  entidad y detalle.
- **RNF-03 Compatibilidad Codespaces**: frontend usa rutas relativas
  `/api/...` + proxy Vite (el navegador no alcanza `localhost:8000`);
  backend escucha en `0.0.0.0:8000`.
- **RNF-04 Arranque seguro**: sin `DATABASE_URL` o con `SECRET_KEY` de ejemplo
  (< 32 caracteres), el backend se niega a arrancar con mensaje claro.
- **RNF-05 Calidad**: CI en cada push/PR (`backend/tests`, SQLite temporal;
  producción sigue en Neon). Cobertura actual: auth, visitas, importación
  xls/xlsx, departamentos, Word, PDF, estadísticas, duplicados/merge.

---

## 5. Modelo de datos (tablas principales)

- **users**: id, email (único), hashed_password, full_name, is_active,
  modules (JSON: asistencia/visitas/adminpro), timestamps.
- **roles/permissions** (+ `roles_permissions`): catálogo extensible.
- **employees**: id, name, department (texto), is_active, timestamps.
- **departments**: id, name (único), is_active, created_at.
- **attendances**: id, employee_id, date, check_in, check_out,
  total_hours (texto), justification_id?, source, timestamps.
- **justifications**: id, employee_id, type, description, start/end_date,
  is_active, timestamps.
- **visitors**: id, first_name, last_name, document_number (índice),
  visited_person?, institution?, visit_justification?, is_verified,
  verified_at?, timestamps.
- **audit_logs**: id, user_id?, action, entity_type, entity_id?, details
  (JSON), ip_address?, timestamps.

Migraciones idempotentes en `backend/migrations/` (`IF NOT EXISTS`):
`001_visitor_visit_fields.sql`, `002_departments.sql`. Se aplican con
`python backend/apply_migrations.py` (lee `DATABASE_URL` de `backend/.env`).

---

## 6. API (prefijos)

| Prefijo | Módulo |
|---|---|
| `/api/v1/auth` | register, login, me |
| `/api/v1/employees` | CRUD, `?department=`, `/duplicates`, `/merge`, `/{id}/toggle-status` |
| `/api/v1/departments` | CRUD + baja lógica con guarda de uso |
| `/api/v1/attendance` | import-excel, lista, stats, chart-data, report-qr, report-docx, public-report |
| `/api/v1/justifications` | CRUD + por empleado |
| `/api/v1/visitors` | registro, QR, **PDF**, verificación, ficha pública |
| `/api/v1/adminpro` | usuarios, cambio de clave, auditoría, estadísticas |

Docs interactivas: `/docs` (solo con backend corriendo).

## 7. Dónde quedan los archivos generados

- **Word/PDF**: **no se guardan en ningún lado**. Se generan en memoria al
  pedirlos y se descargan al navegador (`reporte-asistencia-YYYYMMDD.docx`,
  `visita-<cedula>.pdf`, normalmente a la carpeta Descargas). Cada descarga
  usa los filtros vigentes en ese momento.
- **QR**: se genera al momento (base64 en la respuesta + ficha pública por URL).

---

## 8. Glosario

- **Marcación**: hora de entrada/salida registrada por el ponchador.
- **Fila omitida**: fila del Excel sin entrada ni salida (no genera nada).
- **Fusión**: unificar empleados duplicados conservando uno.
- **Baja lógica**: `is_active=false` sin borrar.
