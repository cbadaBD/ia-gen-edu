#!/usr/bin/env python3
"""
Sube el Programa Curricular Educación Secundaria Perú 2016 (data/curriculo_secundaria_peru_2016.json)
al bucket S3 configurado para Bedrock Knowledge Base (RAG).

Uso:
  cp env.example .env   # configurar AWS_REGION, credenciales
  python upload_curriculo.py

El bucket por defecto es minedu-educacion-peru con prefijo curriculo/
(data-source-config.json: inclusionPrefixes ["curriculo/"]).
Después de subir, sincroniza la Knowledge Base en la consola de Bedrock.
"""
import os
import sys
from pathlib import Path

# Cargar .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Añadir src al path para importar core
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from core.data_ingestion import upload_curriculo_to_s3

if __name__ == "__main__":
    bucket = os.environ.get("S3_CURRICULO_BUCKET", "minedu-educacion-peru")
    ok = upload_curriculo_to_s3(bucket_name=bucket, file_prefix="curriculo/")
    sys.exit(0 if ok else 1)
