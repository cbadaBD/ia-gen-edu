# Usar imagen base de Python
FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivo de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ ./src/
COPY run.py .
COPY env.example .

# Crear directorio para outputs
RUN mkdir -p /app/outputs && chmod 777 /app/outputs

# Configurar variables de entorno
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Exponer puerto de Streamlit
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Comando por defecto
CMD ["python", "-m", "streamlit", "run", "src/app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
