-- 001_visitor_visit_fields.sql
-- Agrega a la tabla visitors: a quién visita, institución de origen y
-- justificación de la visita. Idempotente (IF NOT EXISTS): se puede correr
-- varias veces sin error.
--
-- Cómo aplicarlo (SIN credenciales en archivos; usa tu DATABASE_URL):
--   psql "$DATABASE_URL" -f backend/migrations/001_visitor_visit_fields.sql
-- O pega el contenido en el editor SQL de Neon.
-- En bases NUEVAS no hace falta: create_all ya crea las columnas.

ALTER TABLE visitors ADD COLUMN IF NOT EXISTS visited_person VARCHAR(255);
ALTER TABLE visitors ADD COLUMN IF NOT EXISTS institution VARCHAR(255);
ALTER TABLE visitors ADD COLUMN IF NOT EXISTS visit_justification TEXT;
