#!/bin/bash
# Script para verificar que las credenciales de AWS se están pasando correctamente al contenedor Docker

echo "🔍 Verificando credenciales de AWS en Docker..."
echo ""

# Verificar si el contenedor está corriendo
if ! docker ps | grep -q content_edu_app; then
    echo "❌ El contenedor 'content_edu_app' no está corriendo."
    echo "   Inicia el contenedor con: docker-compose up -d"
    exit 1
fi

echo "✅ Contenedor encontrado"
echo ""

# Verificar variables de entorno dentro del contenedor
echo "📋 Variables de entorno AWS en el contenedor:"
echo "----------------------------------------"
docker exec content_edu_app env | grep AWS | while IFS='=' read -r key value; do
    if [ -n "$value" ]; then
        # Mostrar solo los primeros caracteres de las credenciales por seguridad
        if [[ "$key" == *"SECRET"* ]] || [[ "$key" == *"ACCESS_KEY"* ]]; then
            echo "$key=${value:0:10}... (oculto por seguridad)"
        else
            echo "$key=$value"
        fi
    else
        echo "$key=(vacío)"
    fi
done

echo ""
echo "🧪 Probando creación de cliente Bedrock..."
echo "----------------------------------------"
docker exec content_edu_app python -c "
import os
import sys

# Verificar variables
aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID', '')
aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
aws_region = os.environ.get('AWS_REGION', 'us-east-1')

print(f'AWS_REGION: {aws_region}')
print(f'AWS_ACCESS_KEY_ID: {\"Configurado\" if aws_access_key else \"NO CONFIGURADO\"}')
print(f'AWS_SECRET_ACCESS_KEY: {\"Configurado\" if aws_secret_key else \"NO CONFIGURADO\"}')

if not aws_access_key or not aws_secret_key:
    print('\n❌ ERROR: Las credenciales no están configuradas correctamente')
    sys.exit(1)

# Intentar crear cliente
try:
    import boto3
    client = boto3.client(
        'bedrock-runtime',
        region_name=aws_region,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    print('\n✅ Cliente de Bedrock creado exitosamente')
except Exception as e:
    print(f'\n❌ ERROR al crear cliente: {str(e)}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Todas las verificaciones pasaron correctamente"
else
    echo ""
    echo "❌ Hay problemas con la configuración"
    echo ""
    echo "Solución:"
    echo "1. Verifica que el archivo .env existe en la raíz del proyecto"
    echo "2. Verifica que .env contiene las credenciales correctas:"
    echo "   AWS_ACCESS_KEY_ID=tu_access_key"
    echo "   AWS_SECRET_ACCESS_KEY=tu_secret_key"
    echo "   AWS_REGION=us-east-1"
    echo "3. Reconstruye el contenedor:"
    echo "   docker-compose down"
    echo "   docker-compose up --build -d"
    exit 1
fi
