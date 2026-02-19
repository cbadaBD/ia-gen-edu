import boto3
import json
import os
from pathlib import Path


def upload_curriculo_to_s3(
    bucket_name: str = "minedu-educacion-peru",
    file_prefix: str = "curriculo/",
    curriculo_path: str = None,
) -> bool:
    """
    Sube el JSON del Programa Curricular Secundaria Perú 2016 a S3
    para que Bedrock Knowledge Base pueda ingerirlo (RAG).

    Args:
        bucket_name: Bucket configurado en data-source-config.json (inclusionPrefixes curriculo/)
        file_prefix: Prefijo dentro del bucket (debe coincidir con inclusionPrefixes)
        curriculo_path: Ruta al JSON; si es None, usa data/curriculo_secundaria_peru_2016.json

    Returns:
        True si la carga fue exitosa.
    """
    if curriculo_path is None:
        base = Path(__file__).resolve().parent.parent.parent
        curriculo_path = str(base / "data" / "curriculo_secundaria_peru_2016.json")
    path = Path(curriculo_path)
    if not path.exists():
        print(f"❌ No se encontró el archivo: {curriculo_path}")
        return False
    region = os.environ.get("AWS_REGION", "us-east-1")
    s3_client = boto3.client("s3", region_name=region)
    key = f"{file_prefix.rstrip('/')}/curriculo_secundaria_peru_2016.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            body = f.read()
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json",
        )
        print(f"✅ Currículo subido a s3://{bucket_name}/{key}")
        return True
    except Exception as e:
        print(f"❌ Error al subir currículo a S3: {e}")
        return False
