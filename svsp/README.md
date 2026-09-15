# SVSP — Sistema de Asistencia y Visitas

Backend en **Python (FastAPI)** + Frontend en **React (Vite)** con estética iOS. Arquitectura por capas (routers → services → repositories → models), SOLID, RBAC por módulo, y un rol **AdminPRO** con acceso total.

## Estructura del proyecto

```
svsp/
├── backend/            # API FastAPI
│   └── app/
│       ├── core/       # configuración y seguridad (JWT, hashing)
│       ├── db/         # conexión y sesión de base de datos
│       ├── models/     # entidades SQLAlchemy
│       ├── schemas/    # DTOs Pydantic
│       ├── repositories/  # acceso a datos
│       ├── services/   # reglas de negocio
│       └── routers/    # endpoints REST
├── frontend/           # SPA React (Vite) con estilo iOS
└── docker-compose.yml
```

## Cómo levantar todo en local

1. Copia los archivos de entorno de ejemplo:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```
   Genera un valor real para `SECRET_KEY` en `backend/.env` (cualquier cadena larga aleatoria).

2. Levanta los tres servicios (base de datos, backend y frontend):
   ```bash
   docker compose up --build
   ```

3. Servicios disponibles:
   - Frontend: http://localhost:5173
   - Backend / Swagger (documentación interactiva de la API): http://localhost:8000/docs
   - Base de datos PostgreSQL: localhost:5432 (usuario `svsp_user`, clave `svsp_pass`, db `svsp_db`)

4. Crea las tablas (primera vez) y el primer usuario **AdminPRO**:
   ```bash
   docker compose exec backend python -c "from app.db.base import Base; from app.models import user, employee, attendance, justification, visitor; from app.db.session import engine; Base.metadata.create_all(bind=engine)"
   docker compose exec backend python seed_adminpro.py
   ```
   Sigue las instrucciones en pantalla (correo, nombre y contraseña) y luego inicia sesión con esas credenciales en el frontend.

   > Para producción real, usa migraciones de Alembic (`alembic revision --autogenerate -m "init"` y `alembic upgrade head`) en vez de `create_all`.

## Qué incluye esta primera versión

- **Autenticación JWT** con contraseñas hasheadas (bcrypt).
- **RBAC real en el backend**: cada endpoint valida el módulo (`asistencia`/`visitas`) o exige rol AdminPRO, no solo el frontend.
- **Módulo de Asistencia**: carga de Excel del poncher (columnas Empleado / Hora de entrada / Hora de salida / Horas totales trabajadas), creación automática de empleados, edición de nombre/departamento, inhabilitar/rehabilitar (sin borrado físico), gráfico de empleados por departamento, tarea programada que purga reportes con más de 14 días.
- **Módulo de Visitas**: registro de visitante (nombre, apellido, cédula), generación de código QR en el momento, historial y verificación manual del QR.
- **AdminPRO**: creación de usuarios, asignación de módulos permitidos, inhabilitar/rehabilitar usuarios.
- **Frontend con estética iOS**: barra superior translúcida, tabs inferiores, tarjetas y listas agrupadas, botones tipo pill, tipografía Inter.

## Pendiente para siguientes iteraciones

- Módulo de justificaciones en el frontend (el backend ya expone los endpoints en `/api/justifications`).
- Exportación de reportes a Word/PDF/Excel.
- QR de verificación del reporte de asistencia desde el móvil.
- Bitácora de auditoría de acciones administrativas.
- Migraciones Alembic generadas (`alembic revision --autogenerate`) en vez de `create_all` manual.
- Nginx + HTTPS para el despliegue final en tu servidor propio.
