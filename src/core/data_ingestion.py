import boto3
import json
import os
import datetime

def upload_comments_to_s3(comments_data, bucket_name, file_prefix='comments/'):
    """
    Simula la carga de comentarios (JSON) a S3.
    En un entorno real, los comentarios llegarían de forma continua.
    """
    s3_client = boto3.client('s3', region_name=os.environ['AWS_REGION'])
    
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    file_key = f"{file_prefix}comments_{timestamp_str}.json"
    
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=json.dumps(comments_data, ensure_ascii=False).encode('utf-8'),
            ContentType='application/json'
        )
        print(f" Archivo '{file_key}' cargado a S3 exitosamente.")
        return True
    except Exception as e:
        print(f" Error al cargar a S3: {e}")
        return False

def get_comment_from_s3(bucket_name, file_key):
    """
    Obtiene un archivo JSON de comentarios desde S3.
    (Usado por Lambda o para pruebas directas)
    """
    s3_client = boto3.client('s3', region_name=os.environ['AWS_REGION'])
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response['Body'].read().decode('utf-8')
        return json.loads(file_content)
    except Exception as e:
        print(f" Error al obtener archivo de S3: {e}")
        return None


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
    from pathlib import Path
    if curriculo_path is None:
        base = Path(__file__).resolve().parent.parent.parent
        curriculo_path = str(base / "data" / "curriculo_secundaria_peru_2016.json")
    path = Path(curriculo_path)
    if not path.exists():
        print(f" No se encontró el archivo: {curriculo_path}")
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
        print(f" Currículo subido a s3://{bucket_name}/{key}")
        return True
    except Exception as e:
        print(f" Error al subir currículo a S3: {e}")
        return False