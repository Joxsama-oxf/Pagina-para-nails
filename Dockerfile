FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar algunas librerías de Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del proyecto
COPY . .

# Puerto expuesto (debe coincidir con el del docker-compose.yml)
EXPOSE 8000

# Comando de arranque con gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app:app"]
