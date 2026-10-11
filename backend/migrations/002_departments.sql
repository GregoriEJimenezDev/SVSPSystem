-- 002_departments.sql
-- Crea la tabla departments y siembra los departamentos ya usados en
-- employees.department. Idempotente: se puede correr varias veces.
--
-- Cómo aplicarlo (SIN credenciales en archivos; usa tu DATABASE_URL):
--   python backend/apply_migrations.py
--   (o psql "$DATABASE_URL" -f backend/migrations/002_departments.sql,
--    o pegando el contenido en el editor SQL de Neon).

CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_departments_id ON departments (id);
CREATE INDEX IF NOT EXISTS ix_departments_name ON departments (name);

INSERT INTO departments (name, is_active)
SELECT DISTINCT TRIM(department), TRUE
FROM employees
WHERE department IS NOT NULL AND TRIM(department) <> ''
ON CONFLICT (name) DO NOTHING;
