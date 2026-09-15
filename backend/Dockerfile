FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación
COPY app /app/app
CORE_DIR /app/core
CORE_SEED /app/seed_adminpro.py
ALembic_DIR /app/alembic
INI_FILE /app/alembic.ini

# Variables de entorno por defecto
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear usuario no root
RUN useradd -m -u 1000 appuser
USER appuser

# Puerto de exposición
EXPOSE 8000

# Comando de inicio con recarga para desarrollo
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]