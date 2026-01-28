#!/bin/bash

# Script de configuración del entorno para el proyecto
# Este script instala las dependencias necesarias

echo "🔧 Configurando entorno del proyecto..."

# Verificar si python3-venv está instalado
if ! dpkg -l | grep -q python3-venv; then
    echo "⚠️  python3-venv no está instalado. Ejecuta: sudo apt install python3.12-venv"
    exit 1
fi

# Crear/actualizar entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔌 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

echo "✅ Configuración completada!"
echo ""
echo "Para activar el entorno virtual en el futuro, ejecuta:"
echo "  source venv/bin/activate"
echo ""
echo "Para ejecutar la aplicación:"
echo "  streamlit run src/app/app.py"
