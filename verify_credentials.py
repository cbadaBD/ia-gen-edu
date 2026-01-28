#!/usr/bin/env python3
"""
Script para verificar que las credenciales de AWS están configuradas correctamente.
Útil para verificar la configuración antes de ejecutar la aplicación en Docker.
"""

import os
import sys

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def verificar_credenciales():
    """Verifica que las credenciales de AWS estén configuradas."""
    print("🔍 Verificando credenciales de AWS...\n")
    
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')
    aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
    aws_profile = os.environ.get('AWS_PROFILE')
    
    # Verificar variables de entorno
    print("Variables de entorno encontradas:")
    print(f"  AWS_REGION: {'✅ ' + aws_region if aws_region else '❌ No configurado'}")
    print(f"  AWS_ACCESS_KEY_ID: {'✅ Configurado' if aws_access_key else '❌ No configurado'}")
    print(f"  AWS_SECRET_ACCESS_KEY: {'✅ Configurado' if aws_secret_key else '❌ No configurado'}")
    if aws_session_token:
        print(f"  AWS_SESSION_TOKEN: ✅ Configurado (credenciales temporales)")
    if aws_profile:
        print(f"  AWS_PROFILE: ✅ {aws_profile}")
    print()
    
    # Verificar que las credenciales esenciales estén presentes
    if not aws_access_key or not aws_secret_key:
        print("❌ ERROR: Las credenciales esenciales de AWS no están configuradas.\n")
        print("Por favor, configura las siguientes variables de entorno:")
        print("  - AWS_ACCESS_KEY_ID")
        print("  - AWS_SECRET_ACCESS_KEY")
        print("  - AWS_REGION (opcional, por defecto: us-east-1)\n")
        
        if os.path.exists('.env'):
            print("💡 El archivo .env existe. Verifica que contenga las credenciales correctas.")
        else:
            print("💡 Crea un archivo .env basándote en env.example:")
            print("   cp env.example .env")
            print("   # Luego edita .env con tus credenciales\n")
        
        return False
    
    # Intentar crear un cliente de boto3 para verificar las credenciales
    try:
        import boto3
        print("🔐 Intentando crear cliente de AWS Bedrock...")
        
        client_kwargs = {
            'service_name': 'bedrock-runtime',
            'region_name': aws_region,
            'aws_access_key_id': aws_access_key,
            'aws_secret_access_key': aws_secret_key
        }
        
        if aws_session_token:
            client_kwargs['aws_session_token'] = aws_session_token
        
        bedrock_runtime = boto3.client(**client_kwargs)
        print("✅ Cliente de Bedrock creado exitosamente\n")
        return True
        
    except Exception as e:
        print(f"❌ ERROR al crear cliente de Bedrock: {str(e)}\n")
        print("Verifica que:")
        print("  1. Las credenciales sean correctas")
        print("  2. Tengas permisos para usar Amazon Bedrock")
        print("  3. La región especificada sea correcta")
        print("  4. Bedrock esté habilitado en tu cuenta AWS\n")
        return False

if __name__ == "__main__":
    success = verificar_credenciales()
    sys.exit(0 if success else 1)
