#!/bin/bash

# Script para ejecutar la aplicación Streamlit
# Uso: ./run_streamlit.sh

cd "$(dirname "$0")"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Configurar PYTHONPATH
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# Ejecutar Streamlit
echo "🚀 Iniciando aplicación Streamlit..."
echo "📁 Directorio: ${PWD}"
echo "🌐 Abriendo en: http://localhost:8501"
echo ""

python3 -m streamlit run src/app/app.py --server.port=8501 --server.address=localhost
