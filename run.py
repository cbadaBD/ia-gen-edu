#!/usr/bin/env python3
"""
Script para ejecutar la aplicación Streamlit
Uso: python run.py
"""
import subprocess
import sys
import os
from pathlib import Path

# Cargar variables de entorno si existe .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configurar PYTHONPATH
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Verificar que streamlit esté disponible
try:
    import streamlit
except ImportError:
    print("❌ Error: streamlit no está instalado")
    print("💡 Ejecuta: pip install streamlit")
    sys.exit(1)

# Mostrar información
print("🚀 Iniciando aplicación Streamlit...")
print(f"📁 Directorio: {os.getcwd()}")
print(f"🌐 Abriendo en: http://localhost:8501")
print("")

# Ejecutar Streamlit
os.chdir(Path(__file__).parent)
subprocess.run([
    sys.executable, "-m", "streamlit", "run", 
    "src/app/app.py",
    "--server.port=8501",
    "--server.address=localhost"
])