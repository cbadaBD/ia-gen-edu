import boto3
import json
import os

def generate_summary_bedrock(comments_text_list):
    """
    Genera un resumen conciso de una lista de comentarios usando Amazon Bedrock (Anthropic Claude).
    """
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name=os.environ['AWS_REGION']
    )
    
    comments_str = "\n".join(comments_text_list)
    
    prompt = f"""Actúa como un analista de mercado experto. Lee los siguientes comentarios de clientes sobre un nuevo snack y genera un resumen conciso que destaque las opiniones clave, tanto positivas como negativas, y temas recurrentes.

--- Comentarios ---
{comments_str}
---

Resumen:"""
    
    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.5,
            "top_p": 0.9
        })
        
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId='anthropic.claude-opus-4-6-v1',
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body.get('content', [{}])[0].get('text', "No se pudo generar el resumen.")
    
    except Exception as e:
        print(f"❌ Error al generar resumen con Bedrock: {e}")
        return f"Error al generar el resumen: {e}"