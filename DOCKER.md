# 🐳 Guía de Dockerización del Proyecto

Esta guía explica cómo containerizar y ejecutar el proyecto **Generador de Contenido Educativo AI** usando Docker.

---

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Estructura de Archivos Docker](#estructura-de-archivos-docker)
3. [Configuración Paso a Paso](#configuración-paso-a-paso)
4. [Ejecución del Contenedor](#ejecución-del-contenedor)
5. [Solución de Problemas](#solución-de-problemas)
6. [Producción](#producción)

---

## 🔧 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Docker** (versión 20.10 o superior)
- **Docker Compose** (versión 2.0 o superior) - Opcional pero recomendado

### Verificar Instalación

```bash
docker --version
docker-compose --version
```

---

## 📁 Estructura de Archivos Docker

Necesitarás crear los siguientes archivos en la raíz del proyecto:

```
content_edu/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env
└── ... (resto del proyecto)
```

---

## 🐳 Paso 1: Crear Dockerfile

Crea un archivo `Dockerfile` en la raíz del proyecto:

```dockerfile
# Usar imagen base de Python
FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
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
RUN mkdir -p /app/outputs

# Configurar variables de entorno
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Exponer puerto de Streamlit
EXPOSE 8501

# Comando por defecto
CMD ["python", "-m", "streamlit", "run", "src/app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## 🐙 Paso 2: Crear docker-compose.yml

Crea un archivo `docker-compose.yml` para facilitar la gestión:

```yaml
version: '3.8'

services:
  streamlit-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: content_edu_app
    ports:
      - "8501:8501"
    volumes:
      # Montar carpeta de outputs para persistencia
      - ./outputs:/app/outputs
      # Montar carpeta Desktop del host (opcional)
      - ${HOME}/Desktop/content_edu_outputs:/app/desktop_outputs
    env_file:
      - .env
    environment:
      - PYTHONPATH=/app/src
      - AWS_REGION=${AWS_REGION:-us-east-1}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN:-}
      - AWS_PROFILE=${AWS_PROFILE:-}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## 🚫 Paso 3: Crear .dockerignore

Crea un archivo `.dockerignore` para excluir archivos innecesarios:

```
# Entornos virtuales
venv/
env/
.venv/

# Archivos de Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# Variables de entorno (se pasan via docker-compose)
.env

# Archivos de IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Archivos de sistema
.DS_Store
Thumbs.db

# Logs
*.log

# Archivos temporales
*.tmp
*.temp

# Git
.git/
.gitignore

# Documentación (opcional, puedes incluirlos si quieres)
*.md
!README.md

# Archivos de configuración local
pyrightconfig.json
*.json
!requirements.txt

# Notebooks
*.ipynb

# Scripts de desarrollo
setup.sh
run_streamlit.sh
```

---

## ⚙️ Paso 4: Configurar Variables de Entorno

### Opción A: Usar archivo .env existente

Si ya tienes un archivo `.env`, asegúrate de que contenga:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
```

### Opción B: Crear desde ejemplo

```bash
cp env.example .env
# Editar .env con tus credenciales
nano .env
```

---

## 🚀 Paso 5: Construir la Imagen Docker

### Usando Docker directamente:

```bash
# Construir la imagen
docker build -t content-edu-app:latest .

# Verificar que la imagen se creó
docker images | grep content-edu-app
```

### Usando Docker Compose:

```bash
# Construir y levantar el contenedor
docker-compose up --build

# O solo construir sin levantar
docker-compose build
```

---

## ▶️ Ejecución del Contenedor

### Opción 1: Docker Compose (Recomendado)

```bash
# Iniciar en primer plano
docker-compose up

# Iniciar en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v
```

### Opción 2: Docker directamente

```bash
# Ejecutar contenedor
docker run -d \
  --name content_edu_app \
  -p 8501:8501 \
  --env-file .env \
  -v $(pwd)/outputs:/app/outputs \
  -v ${HOME}/Desktop/content_edu_outputs:/app/desktop_outputs \
  content-edu-app:latest

# Ver logs
docker logs -f content_edu_app

# Detener contenedor
docker stop content_edu_app

# Eliminar contenedor
docker rm content_edu_app
```

---

## 🌐 Acceder a la Aplicación

Una vez que el contenedor esté ejecutándose:

1. **Abre tu navegador** en: `http://localhost:8501`
2. Si estás en un servidor remoto, usa: `http://tu-servidor:8501`

---

## 📊 Comandos Útiles

### Ver estado del contenedor

```bash
# Con Docker Compose
docker-compose ps

# Con Docker
docker ps | grep content_edu
```

### Entrar al contenedor

```bash
# Con Docker Compose
docker-compose exec streamlit-app bash

# Con Docker
docker exec -it content_edu_app bash
```

### Ver logs

```bash
# Con Docker Compose
docker-compose logs -f streamlit-app

# Con Docker
docker logs -f content_edu_app
```

### Reiniciar el contenedor

```bash
# Con Docker Compose
docker-compose restart

# Con Docker
docker restart content_edu_app
```

---

## 🔍 Solución de Problemas

### Problema: El contenedor no inicia

**Solución:**
```bash
# Ver logs de error
docker-compose logs streamlit-app

# Verificar que el puerto no esté en uso
lsof -i :8501

# Cambiar puerto en docker-compose.yml si es necesario
ports:
  - "8502:8501"  # Usar puerto 8502 en el host
```

### Problema: No se pueden leer archivos .env

**Solución:**
```bash
# Verificar que .env existe
ls -la .env

# Verificar permisos
chmod 600 .env

# Verificar formato (sin espacios alrededor del =)
AWS_REGION=us-east-1  # ✅ Correcto
AWS_REGION = us-east-1  # ❌ Incorrecto
```

### Problema: Los outputs no se guardan

**Solución:**
```bash
# Verificar que el volumen está montado
docker inspect content_edu_app | grep Mounts

# Verificar permisos del directorio
mkdir -p outputs
chmod 777 outputs  # O usar tu usuario: chown $USER:$USER outputs
```

### Problema: Error de conexión a AWS Bedrock - "Unable to locate credentials"

Este es uno de los errores más comunes al dockerizar la aplicación. Ocurre cuando las credenciales de AWS no se están pasando correctamente al contenedor.

**Solución paso a paso:**

1. **Verificar que el archivo .env existe y está en la raíz del proyecto:**
```bash
# Verificar que .env existe
ls -la .env

# Si no existe, créalo desde el ejemplo
cp env.example .env
# Luego edita .env con tus credenciales reales
nano .env  # o tu editor preferido
```

2. **Verificar el contenido del archivo .env:**
```bash
# El archivo debe tener este formato (sin espacios alrededor del =):
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=tu_access_key_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui

# ❌ INCORRECTO (con espacios):
AWS_REGION = us-east-1  # Esto NO funcionará
```

3. **Verificar que docker-compose.yml está configurado correctamente:**
```bash
# El docker-compose.yml debe incluir:
env_file:
  - .env
environment:
  - AWS_REGION=${AWS_REGION:-us-east-1}
  - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
  - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
```

4. **Verificar variables de entorno dentro del contenedor:**
```bash
# Ver todas las variables de AWS
docker exec content_edu_app env | grep AWS

# Verificar credenciales específicas (sin mostrar valores completos por seguridad)
docker exec content_edu_app sh -c 'echo "AWS_REGION: $AWS_REGION"; echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."; echo "AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:10}..."'
```

5. **Usar el script de verificación:**
```bash
# Verificar credenciales antes de ejecutar Docker
python verify_credentials.py

# O dentro del contenedor (después de construirlo)
docker exec content_edu_app python verify_credentials.py
```

6. **Reconstruir el contenedor después de cambiar .env:**
```bash
# Si cambiaste el archivo .env, reconstruye el contenedor
docker-compose down
docker-compose up --build -d
```

7. **Verificar que el archivo .env no está en .dockerignore:**
```bash
# El archivo .env NO debe estar listado en .dockerignore
# (Está bien que no se copie a la imagen, pero debe estar disponible para docker-compose)
```

**Nota importante:** El archivo `.env` NO se copia dentro de la imagen Docker por seguridad, pero Docker Compose lo lee desde el host y pasa las variables de entorno al contenedor en tiempo de ejecución.

---

## 🏭 Configuración para Producción

### Dockerfile Optimizado para Producción

```dockerfile
# Multi-stage build para imagen más pequeña
FROM python:3.12-slim as builder

WORKDIR /app

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Imagen final
FROM python:3.12-slim

WORKDIR /app

# Copiar dependencias instaladas
COPY --from=builder /root/.local /root/.local

# Copiar código
COPY src/ ./src/
COPY run.py .

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "src/app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### docker-compose.prod.yml

```yaml
version: '3.8'

services:
  streamlit-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: content_edu_app_prod
    ports:
      - "8501:8501"
    volumes:
      - ./outputs:/app/outputs:rw
    env_file:
      - .env.production
    environment:
      - PYTHONPATH=/app/src
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

### Ejecutar en Producción

```bash
# Construir y ejecutar
docker-compose -f docker-compose.prod.yml up -d --build

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🔐 Seguridad

### Buenas Prácticas

1. **No incluir .env en la imagen Docker**
   - Usar `--env-file` o variables de entorno
   - El `.dockerignore` ya excluye `.env`

2. **Usar secretos de Docker** (para producción)
   ```bash
   docker secret create aws_access_key_id <(echo "tu_key")
   ```

3. **Ejecutar como usuario no-root**
   - El Dockerfile de producción ya incluye esto

4. **Limitar recursos**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 2G
   ```

---

## 📝 Resumen de Comandos Rápidos

```bash
# Construir imagen
docker build -t content-edu-app .

# Ejecutar con Docker Compose
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down

# Reconstruir después de cambios
docker-compose up -d --build

# Limpiar todo
docker-compose down -v
docker system prune -a
```

---

## 🎯 Checklist de Dockerización

- [ ] Dockerfile creado
- [ ] docker-compose.yml creado
- [ ] .dockerignore creado
- [ ] Archivo .env configurado con credenciales AWS
- [ ] Imagen construida exitosamente
- [ ] Contenedor ejecutándose
- [ ] Aplicación accesible en http://localhost:8501
- [ ] Outputs se guardan correctamente
- [ ] Conexión a AWS Bedrock funcionando

---

## 📚 Recursos Adicionales

- [Documentación oficial de Docker](https://docs.docker.com/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
- [Streamlit en Docker](https://docs.streamlit.io/knowledge-base/tutorials/docker)

---

**Última actualización**: 2026-01-16
