import boto3
import json
import os
import re
from botocore.exceptions import NoCredentialsError, ClientError

# Cargar variables de entorno desde .env si existe (solo en desarrollo local)
# En Docker, las variables se pasan directamente desde docker-compose.yml
try:
    from dotenv import load_dotenv
    # Intentar cargar .env solo si existe (no falla si no existe)
    import pathlib
    env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except (ImportError, Exception):
    # Si no hay dotenv o hay algún error, continuar (las variables pueden venir del sistema)
    pass

def crear_cliente_bedrock():
    """
    Crea un cliente de Bedrock con manejo adecuado de credenciales.
    
    Returns:
        Cliente de bedrock-runtime configurado
        
    Raises:
        Exception: Si no se pueden encontrar las credenciales de AWS
    """
    # Verificar que las credenciales estén disponibles
    aws_access_key = (os.environ.get('AWS_ACCESS_KEY_ID') or os.environ.get('AWS_ACCESS_KEY') or '').strip()
    aws_secret_key = (os.environ.get('AWS_SECRET_ACCESS_KEY') or os.environ.get('AWS_SECRET_KEY') or '').strip()
    aws_session_token = (os.environ.get('AWS_SESSION_TOKEN') or '').strip() or None
    aws_region = (os.environ.get('AWS_REGION') or 'us-east-1').strip()
    aws_profile = (os.environ.get('AWS_PROFILE') or '').strip() or None
    
    # Si hay credenciales en variables de entorno, usarlas explícitamente
    if aws_access_key and aws_secret_key:
        try:
            client_kwargs = {
                'service_name': 'bedrock-runtime',
                'region_name': aws_region,
                'aws_access_key_id': aws_access_key,
                'aws_secret_access_key': aws_secret_key
            }
            
            # Agregar session token si está presente (para credenciales temporales)
            if aws_session_token:
                client_kwargs['aws_session_token'] = aws_session_token
            
            bedrock_runtime = boto3.client(**client_kwargs)
            # Validar que el cliente funcione intentando obtener credenciales
            try:
                bedrock_runtime._client_config.credentials
            except:
                pass  # Si no puede obtener credenciales aquí, se validará al usarlo
            return bedrock_runtime
        except Exception as e:
            error_msg = (
                f"❌ Error al crear cliente de Bedrock con credenciales explícitas: {str(e)}\n\n"
                "Verifica que:\n"
                "1. Las credenciales de AWS sean correctas\n"
                "2. Tengas permisos para usar Amazon Bedrock\n"
                "3. La región especificada sea correcta\n"
                "4. Bedrock esté habilitado en tu cuenta AWS\n"
            )
            raise Exception(error_msg)
    
    # Si no hay credenciales en variables de entorno, intentar usar perfil de AWS o credenciales por defecto
    try:
        # Si hay un perfil especificado, usarlo
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            # Validar que el perfil tenga credenciales antes de crear el cliente
            credentials = session.get_credentials()
            if not credentials:
                raise Exception(f"No se encontraron credenciales para el perfil '{aws_profile}'")
            bedrock_runtime = session.client(
                service_name='bedrock-runtime',
                region_name=aws_region
            )
        else:
            # Intentar usar credenciales por defecto de AWS (desde ~/.aws/credentials o IAM role)
            session = boto3.Session()
            # Validar que haya credenciales disponibles antes de crear el cliente
            credentials = session.get_credentials()
            if not credentials:
                raise Exception("No se encontraron credenciales de AWS en el sistema")
            bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=aws_region
            )
        
        # Validar que el cliente tenga credenciales válidas intentando acceder a ellas
        try:
            # Intentar obtener las credenciales del cliente para validar que estén disponibles
            if hasattr(bedrock_runtime, '_client_config'):
                client_credentials = bedrock_runtime._client_config.credentials
                if not client_credentials:
                    # Si no hay credenciales en el cliente, intentar obtenerlas de la sesión
                    if not credentials:
                        raise Exception("No se pudieron obtener credenciales válidas del cliente")
        except AttributeError:
            # Si no tiene _client_config, verificar las credenciales de la sesión
            if not credentials:
                raise Exception("No se encontraron credenciales válidas")
        except Exception:
            # Si hay algún error al validar, verificar las credenciales de la sesión
            if not credentials:
                raise Exception("No se encontraron credenciales válidas")
        
        return bedrock_runtime
        
    except Exception as e:
        # Diagnosticar qué variables están disponibles
        env_vars = {k: ('Configurado' if v and v.strip() else 'Vacío o no configurado') 
                   for k, v in os.environ.items() if 'AWS' in k}
        env_info = "\n".join([f"  {k}: {v}" for k, v in env_vars.items()]) if env_vars else "  Ninguna variable AWS encontrada"
        
        error_msg = (
            "❌ Error: No se encontraron credenciales de AWS.\n\n"
            f"Variables de entorno detectadas:\n{env_info if env_info else '  Ninguna variable AWS encontrada'}\n\n"
            "Por favor, configura tus credenciales de una de las siguientes formas:\n\n"
            "1. Crear archivo .env en la raíz del proyecto con:\n"
            "   AWS_ACCESS_KEY_ID=tu_access_key\n"
            "   AWS_SECRET_ACCESS_KEY=tu_secret_key\n"
            "   AWS_REGION=us-east-1\n\n"
            "2. Configurar variables de entorno del sistema:\n"
            "   export AWS_ACCESS_KEY_ID=tu_access_key\n"
            "   export AWS_SECRET_ACCESS_KEY=tu_secret_key\n"
            "   export AWS_REGION=us-east-1\n\n"
            "3. Configurar perfil de AWS (~/.aws/credentials):\n"
            "   aws configure\n\n"
            "4. Si usas Docker, asegúrate de que:\n"
            "   - El archivo .env existe en la raíz del proyecto\n"
            "   - docker-compose.yml tiene: env_file: - .env\n"
            "   - Las variables están en la sección environment:\n"
            "     environment:\n"
            "       - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}\n"
            "       - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}\n"
            "   - Reconstruye el contenedor: docker-compose down && docker-compose up --build\n\n"
            f"Error detallado: {str(e)}"
        )
        raise Exception(error_msg)

def limpiar_contenido_html(contenido):
    """
    Limpia etiquetas HTML y viñetas del contenido generado preservando el formato de tabla.
    
    Args:
        contenido: Texto que puede contener etiquetas HTML y viñetas
        
    Returns:
        Texto limpio sin etiquetas HTML ni viñetas, preservando formato de tabla
    """
    if not contenido:
        return contenido
    
    # Primero, proteger las líneas de tabla (que contienen |)
    lineas = contenido.split('\n')
    lineas_procesadas = []
    
    for linea in lineas:
        # Si es una línea de tabla, limpiar HTML y viñetas pero preservar estructura
        if '|' in linea:
            # Reemplazar <br> dentro de celdas con espacios
            linea = re.sub(r'<br\s*/?>', ' ', linea, flags=re.IGNORECASE)
            # Eliminar otras etiquetas HTML pero mantener el contenido
            linea = re.sub(r'<[^>]+>', '', linea)
            # Eliminar viñetas (•, -, *, →, etc.) al inicio de líneas dentro de celdas
            # Buscar viñetas seguidas de espacio dentro del contenido de la celda
            # Patrón: viñeta al inicio después de | o después de salto de línea dentro de la celda
            partes = linea.split('|')
            if len(partes) >= 3:  # Tiene al menos item | contenido |
                # Procesar solo el contenido (partes[1])
                contenido_celda = partes[1]
                # Eliminar viñetas al inicio de líneas dentro del contenido
                contenido_celda = re.sub(r'^[\s]*[•\-\*→▪▫○●]\s*', '', contenido_celda, flags=re.MULTILINE)
                # Eliminar viñetas en medio del texto (con espacio antes)
                contenido_celda = re.sub(r'\s+[•\-\*→▪▫○●]\s+', ' ', contenido_celda)
                contenido_celda = re.sub(r'\s+[•\-\*→▪▫○●]\s*', ' ', contenido_celda)
                # Reconstruir la línea
                partes[1] = contenido_celda
                linea = '|'.join(partes)
            # Limpiar espacios múltiples pero preservar la estructura de la tabla
            linea = re.sub(r' +', ' ', linea)
            lineas_procesadas.append(linea)
        else:
            # Para líneas que no son tabla, reemplazar <br> con saltos de línea
            linea = re.sub(r'<br\s*/?>', '\n', linea, flags=re.IGNORECASE)
            # Reemplazar </p> con salto de línea
            linea = re.sub(r'</p>', '\n', linea, flags=re.IGNORECASE)
            # Reemplazar <p> con salto de línea
            linea = re.sub(r'<p[^>]*>', '\n', linea, flags=re.IGNORECASE)
            # Eliminar otras etiquetas HTML
            linea = re.sub(r'<[^>]+>', '', linea)
            # Eliminar viñetas
            linea = re.sub(r'^[\s]*[•\-\*→▪▫○●]\s*', '', linea)
            linea = re.sub(r'\s+[•\-\*→▪▫○●]\s+', ' ', linea)
            lineas_procesadas.append(linea)
    
    contenido = '\n'.join(lineas_procesadas)
    
    # Limpiar múltiples saltos de línea consecutivos (máximo 2) pero solo fuera de líneas de tabla
    lineas_finales = []
    for linea in contenido.split('\n'):
        if '|' in linea:
            # Líneas de tabla: mantener como están
            lineas_finales.append(linea)
        else:
            # Líneas normales: agregar solo si no es vacía
            if linea.strip():
                lineas_finales.append(linea.strip())
    
    return '\n'.join(lineas_finales)

def validar_y_corregir_formato_tabla(contenido):
    """
    Valida y corrige el formato de la tabla para asegurar que todo el contenido esté dentro de las celdas.
    Mueve agresivamente todo el contenido suelto dentro de las celdas correspondientes.
    También valida que ITEM esté siempre a la izquierda y CONTENIDO a la derecha.
    
    Args:
        contenido: Texto que debería ser una tabla
        
    Returns:
        Contenido corregido con formato de tabla válido
    """
    if not contenido:
        return contenido
    
    # Primero validar y corregir el orden de las columnas
    contenido = validar_orden_columnas_tabla(contenido)
    
    lineas = contenido.split('\n')
    lineas_corregidas = []
    dentro_tabla = False
    ultima_fila_tabla_idx = -1
    contenido_suelto_actual = []
    
    i = 0
    while i < len(lineas):
        linea_original = lineas[i]
        linea = linea_original.strip()
        
        # Detectar inicio de tabla
        if '| ITEM | CONTENIDO |' in linea or '|------|-----------|' in linea:
            dentro_tabla = True
            # Procesar cualquier contenido suelto acumulado antes de la tabla
            if contenido_suelto_actual:
                contenido_suelto_actual = []  # Descartar contenido antes de la tabla
            lineas_corregidas.append(linea)
            i += 1
            continue
        
        # Si estamos dentro de la tabla
        if dentro_tabla:
            # Verificar si es una línea de tabla (tiene | y al menos 2 columnas)
            if '|' in linea:
                # Primero procesar contenido suelto acumulado convirtiéndolo en filas de tabla
                if contenido_suelto_actual:
                    for contenido_suelto in contenido_suelto_actual:
                        if contenido_suelto.strip():
                            fila_tabla = f"| | {contenido_suelto.strip()} |"
                            lineas_corregidas.append(fila_tabla)
                    contenido_suelto_actual = []
                
                # Verificar que tenga el formato correcto de tabla
                # Contar las barras | para verificar estructura
                num_barras = linea.count('|')
                if num_barras >= 2:
                    # Es una fila válida de tabla
                    lineas_corregidas.append(linea)
                    ultima_fila_tabla_idx = len(lineas_corregidas) - 1
                else:
                    # No es una fila válida, convertir en fila de tabla con item vacío
                    if linea:
                        fila_tabla = f"| | {linea} |"
                        lineas_corregidas.append(fila_tabla)
                        ultima_fila_tabla_idx = len(lineas_corregidas) - 1
            else:
                # Línea sin |, es contenido suelto que debe convertirse en fila de tabla
                if linea:  # Solo agregar si no está vacía
                    # Convertir contenido suelto en fila de tabla con item vacío
                    fila_tabla = f"| | {linea} |"
                    lineas_corregidas.append(fila_tabla)
                    ultima_fila_tabla_idx = len(lineas_corregidas) - 1
                    contenido_suelto_actual = []  # Ya se procesó
        else:
            # Contenido antes de la tabla, ignorar completamente
            pass
        
        i += 1
    
    # Procesar cualquier contenido suelto restante al final convirtiéndolo en filas de tabla
    if contenido_suelto_actual:
        for contenido_suelto in contenido_suelto_actual:
            if contenido_suelto.strip():
                fila_tabla = f"| | {contenido_suelto.strip()} |"
                lineas_corregidas.append(fila_tabla)
    
    # Si no hay tabla detectada, retornar el contenido original
    if not dentro_tabla:
        return contenido
    
    # Asegurar que solo haya líneas de tabla en el resultado
    resultado_final = []
    for linea in lineas_corregidas:
        if '|' in linea or not linea.strip():
            resultado_final.append(linea)
        # Si hay una línea sin | después de la tabla, convertirla en fila de tabla con item vacío
        elif resultado_final and dentro_tabla and linea.strip():
            # Convertir contenido suelto en fila de tabla con item vacío a la izquierda
            fila_tabla = f"| | {linea.strip()} |"
            resultado_final.append(fila_tabla)
    
    resultado = '\n'.join(resultado_final)
    # Validar nuevamente el orden después de la corrección
    return validar_orden_columnas_tabla(resultado)

def extraer_titulo_unidad_didactica(contenido):
    """
    Extrae el título de la unidad didáctica de la tabla generada.
    
    Args:
        contenido: Contenido de la unidad didáctica en formato de tabla
        
    Returns:
        Título de la unidad didáctica o None si no se encuentra
    """
    if not contenido:
        return None
    
    lineas = contenido.split('\n')
    for linea in lineas:
        # Buscar la fila con TÍTULO DE LA UNIDAD DIDÁCTICA
        if 'TÍTULO' in linea.upper() and 'UNIDAD' in linea.upper() and '|' in linea:
            partes = linea.split('|')
            if len(partes) >= 3:
                # El título está en la segunda columna (índice 1)
                titulo = partes[1].strip()
                # Limpiar posibles etiquetas HTML o formato
                titulo = re.sub(r'<[^>]+>', '', titulo)
                titulo = re.sub(r'\*\*', '', titulo)
                titulo = titulo.strip()
                if titulo:
                    return titulo
        # También buscar directamente en el contenido de la celda
        if '| **TÍTULO' in linea.upper() or '| TÍTULO' in linea.upper():
            partes = linea.split('|')
            if len(partes) >= 3:
                titulo = partes[2].strip()
                titulo = re.sub(r'<[^>]+>', '', titulo)
                titulo = re.sub(r'\*\*', '', titulo)
                titulo = titulo.strip()
                if titulo:
                    return titulo
    
    return None

def extraer_titulos_sesiones_unidad(contenido):
    """
    Extrae los títulos de las sesiones de aprendizaje de la unidad didáctica.
    
    Args:
        contenido: Contenido de la unidad didáctica en formato de tabla
        
    Returns:
        Lista de títulos de sesiones encontrados
    """
    titulos_sesiones = []
    if not contenido:
        return titulos_sesiones
    
    lineas = contenido.split('\n')
    dentro_secuencia = False
    
    for linea in lineas:
        # Buscar la sección de SECUENCIA DE SESIONES
        if 'SECUENCIA' in linea.upper() and 'SESION' in linea.upper():
            dentro_secuencia = True
            # Extraer títulos de esta línea si están presentes
            if '|' in linea:
                partes = linea.split('|')
                if len(partes) >= 3:
                    contenido_celda = partes[1].strip() if len(partes) > 1 else ''
                    # Buscar patrones como "Sesión 1: [título]" o "Sesión 1 - [título]"
                    matches = re.findall(r'Sesi[oó]n\s+\d+[:\-]\s*([^\n\.]+)', contenido_celda, re.IGNORECASE)
                    titulos_sesiones.extend([m.strip() for m in matches if m.strip()])
            continue
        
        # Si estamos dentro de la secuencia, buscar más títulos
        if dentro_secuencia and '|' in linea:
            partes = linea.split('|')
            if len(partes) >= 3:
                contenido_celda = partes[1].strip() if len(partes) > 1 else ''
                # Buscar patrones de sesiones
                matches = re.findall(r'Sesi[oó]n\s+\d+[:\-]\s*([^\n\.]+)', contenido_celda, re.IGNORECASE)
                titulos_sesiones.extend([m.strip() for m in matches if m.strip()])
    
    # Si no se encontraron en formato estructurado, buscar en todo el contenido
    if not titulos_sesiones:
        contenido_completo = '\n'.join(lineas)
        # Buscar patrones más flexibles
        matches = re.findall(r'Sesi[oó]n\s+\d+[:\-]\s*([^\n\.]+)', contenido_completo, re.IGNORECASE)
        titulos_sesiones = [m.strip() for m in matches if m.strip() and len(m.strip()) > 5]
    
    # Limpiar títulos de etiquetas HTML y formato
    titulos_limpios = []
    for titulo in titulos_sesiones:
        titulo_limpio = re.sub(r'<[^>]+>', '', titulo)
        titulo_limpio = re.sub(r'\*\*', '', titulo_limpio)
        titulo_limpio = titulo_limpio.strip()
        if titulo_limpio and len(titulo_limpio) > 5:
            titulos_limpios.append(titulo_limpio)
    
    return titulos_limpios

def validar_orden_columnas_tabla(contenido):
    """
    Valida y corrige el orden de las columnas en las tablas para asegurar que
    ITEM siempre esté a la izquierda y CONTENIDO a la derecha.
    Solo corrige tablas con formato | ITEM | CONTENIDO |, no afecta otras tablas.
    
    Args:
        contenido: Texto que contiene tablas en formato markdown
        
    Returns:
        Contenido con el orden de columnas corregido si es necesario
    """
    if not contenido:
        return contenido
    
    lineas = contenido.split('\n')
    lineas_corregidas = []
    orden_invertido_detectado = False
    dentro_tabla_item_contenido = False
    
    for linea in lineas:
        linea_stripped = linea.strip()
        
        # Solo procesar líneas que parecen ser filas de tabla (contienen |)
        if '|' in linea_stripped:
            # Dividir por | para obtener las partes
            partes_completas = linea_stripped.split('|')
            # Limpiar espacios en blanco pero mantener estructura
            partes = [p.strip() for p in partes_completas]
            
            # Verificar si es una tabla de formato | ITEM | CONTENIDO |
            if len(partes) >= 3:  # Al menos | col1 | col2 |
                primera_col = partes[1].upper() if len(partes) > 1 else ''
                segunda_col = partes[2].upper() if len(partes) > 2 else ''
                
                # Detectar si es una tabla de formato ITEM | CONTENIDO
                es_tabla_item_contenido = (
                    ('ITEM' in primera_col and 'CONTENIDO' in segunda_col) or
                    ('CONTENIDO' in primera_col and 'ITEM' in segunda_col) or
                    dentro_tabla_item_contenido
                )
                
                # Si es una tabla de formato ITEM | CONTENIDO, procesarla
                if es_tabla_item_contenido:
                    dentro_tabla_item_contenido = True
                    
                    # Detectar orden correcto en encabezado
                    if 'ITEM' in primera_col and 'CONTENIDO' in segunda_col:
                        orden_invertido_detectado = False
                    
                    # Detectar orden invertido en encabezado
                    elif 'CONTENIDO' in primera_col and 'ITEM' in segunda_col:
                        orden_invertido_detectado = True
                        # Invertir las primeras dos columnas de contenido
                        partes[1], partes[2] = partes[2], partes[1]
                    
                    # Detectar separador y verificar orden basado en longitud
                    elif all(c in '-: ' for c in primera_col) and all(c in '-: ' for c in segunda_col):
                        # Es un separador, verificar si está invertido
                        if orden_invertido_detectado or (len(primera_col) > len(segunda_col) and not ('ITEM' in primera_col or 'CONTENIDO' in primera_col)):
                            # Separador invertido, corregir
                            partes[1], partes[2] = partes[2], partes[1]
                            orden_invertido_detectado = False
                    
                    # Si detectamos orden invertido previamente y esta es una fila de datos
                    elif orden_invertido_detectado and len(partes) >= 3:
                        # Invertir las primeras dos columnas de contenido
                        partes[1], partes[2] = partes[2], partes[1]
                    
                    # Reconstruir la línea manteniendo el formato original
                    # Preservar espacios alrededor de las barras |
                    linea_corregida = '|'
                    for i, parte in enumerate(partes):
                        if i == 0:
                            continue  # Saltar la primera parte vacía antes del primer |
                        if parte:  # Solo agregar si hay contenido
                            linea_corregida += ' ' + parte + ' |'
                        else:
                            linea_corregida += ' |'
                    lineas_corregidas.append(linea_corregida)
                else:
                    # No es una tabla ITEM | CONTENIDO, mantenerla como está
                    lineas_corregidas.append(linea_stripped)
                    dentro_tabla_item_contenido = False
                    orden_invertido_detectado = False
            else:
                # Mantener la línea como está si no tiene el formato esperado
                lineas_corregidas.append(linea_stripped)
        else:
            # Líneas que no son tabla, mantenerlas como están
            # Si salimos de una tabla, resetear el estado
            dentro_tabla_item_contenido = False
            orden_invertido_detectado = False
            lineas_corregidas.append(linea_stripped)
    
    return '\n'.join(lineas_corregidas)

def limpieza_final_tabla(contenido):
    """
    Hace una pasada final más agresiva para asegurar que TODO el contenido esté dentro de las celdas.
    Elimina cualquier línea que no sea parte de la tabla.
    
    Args:
        contenido: Texto que debería ser una tabla
        
    Returns:
        Contenido con solo líneas de tabla válidas
    """
    if not contenido:
        return contenido
    
    # Primero validar y corregir el orden de las columnas
    contenido = validar_orden_columnas_tabla(contenido)
    
    lineas = contenido.split('\n')
    lineas_finales = []
    dentro_tabla = False
    
    for linea in lineas:
        linea_stripped = linea.strip()
        
        # Detectar inicio de tabla
        if '| ITEM | CONTENIDO |' in linea_stripped or '|------|-----------|' in linea_stripped:
            dentro_tabla = True
            lineas_finales.append(linea_stripped)
            continue
        
        if dentro_tabla:
            # Solo incluir líneas que tengan | (son parte de la tabla)
            if '|' in linea_stripped:
                lineas_finales.append(linea_stripped)
            # Si no tiene | pero estamos dentro de la tabla, convertir en fila de tabla con item vacío
            elif linea_stripped:
                # Convertir contenido suelto en fila de tabla con item vacío a la izquierda
                fila_tabla = f"| | {linea_stripped} |"
                lineas_finales.append(fila_tabla)
    
    resultado = '\n'.join(lineas_finales)
    # Validar nuevamente el orden después de la limpieza
    return validar_orden_columnas_tabla(resultado)

# Función principal para generar programación curricular
def generar_programacion_curricular(grado_secundaria, competencia, capacidades, contenidos, num_iteraciones=3, contenido_referencia=None):
    """
    Genera una programación curricular completa para Ciencia y Tecnología 
    utilizando un modelo de lenguaje de Bedrock con técnica de auto-crítica
    y llamadas iterativas a la API.
    
    Args:
        grado_secundaria: Grado de secundaria (3, 4 o 5)
        competencia: Competencia principal
        capacidades: Capacidades específicas
        contenidos: Contenidos curriculares
        num_iteraciones: Número de iteraciones de mejora (default: 3)
        contenido_referencia: Contenido opcional de un archivo DOCX subido como referencia
    """
    try:
        bedrock_runtime = crear_cliente_bedrock()
       
        # --- PASO 1: Generar la programación inicial ---
        # Construir prompt con o sin referencia de archivo
        contexto_referencia = ""
        if contenido_referencia and len(contenido_referencia.strip()) > 0:
            # Limitar el tamaño del contenido de referencia para no exceder límites
            contenido_ref_limitado = contenido_referencia[:3000] if len(contenido_referencia) > 3000 else contenido_referencia
            contexto_referencia = f"""

DOCUMENTO DE REFERENCIA:
---
El usuario ha proporcionado un documento de referencia con información curricular. Úsalo como base para generar la programación, pero asegúrate de adaptarla a los requerimientos específicos indicados abajo.

CONTENIDO DEL DOCUMENTO DE REFERENCIA:
{contenido_ref_limitado}
---
"""
        
        prompt_inicial = f"""
Actúa como especialista en programación curricular. Tu tarea es crear una tabla de programación educativa para estudiantes de {grado_secundaria}º de secundaria del área de Ciencia y Tecnología.

CRÍTICO: Debes generar SOLO tablas con formato estricto. TODO el contenido debe estar DENTRO de las celdas de las tablas. NO generes nada fuera de la estructura de tabla. NO agregues texto antes o después de las tablas.

{contexto_referencia}

INFORMACIÓN BASE:
---
GRADO: {grado_secundaria}º de secundaria
COMPETENCIA: {competencia}
CAPACIDADES: {capacidades}
CONTENIDOS: {contenidos}
---

INSTRUCCIONES PARA COMPLETAR:
1. Transcribe exactamente la COMPETENCIA y CAPACIDADES proporcionadas
2. Organiza los CONTENIDOS por bloques temáticos (Física, Química)
3. Genera DESEMPEÑOS específicos para {grado_secundaria}º de secundaria que sean:
   - Observables y medibles en el aula
   - Relacionados directamente con los contenidos
   - Apropiados para la edad de los estudiantes
   - Que reflejen las 5 capacidades de indagación científica
   - Entre 12-15 desempeños específicos
4. Crea CRITERIOS DE EVALUACIÓN que permitan medir cada desempeño (2-3 criterios por desempeño)
5. Propón INSTRUMENTOS DE EVALUACIÓN variados:
   - Rúbricas de indagación científica
   - Listas de cotejo para experimentos
   - Escalas de valoración para informes
   - Evaluaciones escritas
   - Portafolios de evidencias
   - Prácticas de laboratorio
6. Presenta todo en formato de tabla clara y organizada
7. Al final incluye secciones adicionales en formato de tabla:
   - COMPETENCIAS TRANSVERSALES (Se desenvuelve en entornos virtuales y Gestiona su aprendizaje)
   - ENFOQUES TRANSVERSALES (con valores y comportamientos observables)
   - SECUENCIA DE 6 SESIONES DE APRENDIZAJE (con títulos y actividades principales)

CONSIDERACIONES IMPORTANTES:
- Los desempeños deben ser actuaciones específicas que demuestren progreso en el aprendizaje
- Considera la progresión del aprendizaje según el grado educativo
- Incluye aspectos de indagación científica apropiados para la edad
- Los instrumentos deben ser prácticos de implementar en el aula

FORMATO REQUERIDO - TABLA PRINCIPAL:
TU RESPUESTA DEBE COMENZAR EXACTAMENTE CON: | COMPETENCIA | CAPACIDADES | CONTENIDOS | DESEMPEÑOS | CRITERIOS DE EVALUACIÓN | INSTRUMENTOS DE EVALUACIÓN |

Para la tabla principal, usa este formato:
| COMPETENCIA | CAPACIDADES | CONTENIDOS | DESEMPEÑOS | CRITERIOS DE EVALUACIÓN | INSTRUMENTOS DE EVALUACIÓN |
|-------------|-------------|------------|------------|------------------------|---------------------------|
| [contenido] | [contenido] | [contenido] | [contenido] | [contenido] | [contenido] |

Cada fila debe estar en una línea separada, usando | para separar las columnas. Asegúrate de que todas las filas tengan el mismo número de columnas.

Para las secciones adicionales (COMPETENCIAS TRANSVERSALES, ENFOQUES TRANSVERSALES, SECUENCIA DE SESIONES), usa el formato de tabla:
IMPORTANTE: El formato debe ser EXACTAMENTE | ITEM | CONTENIDO | donde ITEM va a la IZQUIERDA y CONTENIDO a la DERECHA.

| ITEM | CONTENIDO |
|------|-----------|
| **COMPETENCIAS TRANSVERSALES** | [contenido completo dentro de esta celda] |
| **ENFOQUES TRANSVERSALES** | [contenido completo dentro de esta celda] |
| **SECUENCIA DE SESIONES DE APRENDIZAJE** | Sesión 1: [título completo]. Actividades: [descripción]. Sesión 2: [título completo]. Actividades: [descripción]. [continuar con todas las sesiones, todo dentro de esta celda] |

CRÍTICO: NUNCA inviertas el orden. ITEM siempre a la izquierda, CONTENIDO siempre a la derecha.

REGLAS ESTRICTAS DE FORMATO:
1. SOLO genera tablas con el formato exacto mostrado arriba
2. TODO el contenido debe estar dentro de las celdas de las tablas
3. NO generes títulos, subtítulos o contenido fuera de las tablas
4. NO uses etiquetas HTML (<br>, <p>, etc.)
5. NO uses viñetas (•, -, *, →, etc.) - SOLO texto plano dentro de las celdas
6. Para separar contenido dentro de una celda, usa saltos de línea reales
7. Para subsecciones dentro de una celda, usa texto plano con saltos de línea, NO listas con viñetas
8. Todas las secciones deben estar en formato de tabla
"""
        
        # Ajustar parámetros del modelo (formato Claude 3)
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt_inicial
                }
            ],
            "temperature": 0.7,
            "top_p": 0.9
        })
       
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        # Claude 3 devuelve la respuesta en content[0].text
        ultima_programacion = response_body.get('content', [{}])[0].get('text', '')
        
        # Agregar logging para debug
        print(f"Respuesta inicial - Longitud: {len(ultima_programacion) if ultima_programacion else 0}")
        print(f"Primeros 500 caracteres: {ultima_programacion[:500] if ultima_programacion else 'None'}")
       
        # --- PASO 2: Bucle de mejora recursiva (llamadas iterativas) ---
        for i in range(num_iteraciones):
            criterios = [
                "Revisa la programación anterior y mejora la especificidad de los desempeños para que sean más observables y medibles en el contexto educativo. Cada desempeño debe describir claramente qué hará el estudiante.",
                "Analiza la coherencia entre contenidos, desempeños y criterios de evaluación. Verifica que cada criterio permita evaluar efectivamente el desempeño correspondiente y que estén perfectamente alineados.",
                "Revisa y mejora los instrumentos de evaluación para que sean variados, pertinentes y prácticos de implementar en el aula. Incluye tanto instrumentos formativos como sumativos."
            ]
            criterio_actual = criterios[i % len(criterios)]
           
            # El prompt de cada iteración incluye la programación anterior
            prompt_mejora = f"""
Eres un especialista en programación curricular y evaluación educativa. 

Aquí tienes la programación curricular que necesita mejoras:
---
{ultima_programacion}
---

Basándote en la programación anterior, genera una nueva y mejorada versión. Enfócate específicamente en: "{criterio_actual}"

CRÍTICO: Debes generar SOLO tablas con formato estricto. TODO el contenido debe estar DENTRO de las celdas de las tablas. NO generes nada fuera de la estructura de tabla.

MANTENER:
- El formato de tabla exacto con las 6 columnas para la tabla principal
- Todas las secciones adicionales en formato de tabla (competencias transversales, enfoques, sesiones)
- La estructura general del documento
- El formato de tabla con | ITEM | CONTENIDO | para secciones adicionales (ITEM a la IZQUIERDA, CONTENIDO a la DERECHA)
- NUNCA invertir el orden de las columnas: ITEM siempre a la izquierda, CONTENIDO siempre a la derecha

MEJORAR:
- La calidad pedagógica del contenido según el criterio especificado
- La pertinencia para estudiantes de {grado_secundaria}º de secundaria
- La claridad y precisión de los elementos a evaluar
- La viabilidad de implementación práctica

REGLAS ESTRICTAS:
1. SOLO genera tablas con el formato exacto
2. TODO el contenido debe estar dentro de las celdas de las tablas
3. NO generes títulos, subtítulos o contenido fuera de las tablas
4. NO uses etiquetas HTML
5. NO uses viñetas - SOLO texto plano dentro de las celdas

Conserva el formato de tabla completo y mejora la calidad del contenido educativo.
"""
           
            body_mejora = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt_mejora
                    }
                ],
                "temperature": 0.7,
                "top_p": 0.9
            })
           
            response_mejora = bedrock_runtime.invoke_model(
                body=body_mejora,
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                accept='application/json',
                contentType='application/json'
            )
            
            response_body_mejora = json.loads(response_mejora.get('body').read())
            # Claude 3 devuelve la respuesta en content[0].text
            nueva_programacion = response_body_mejora.get('content', [{}])[0].get('text', '')
            
            # Verificar que la nueva respuesta sea válida antes de actualizar
            if nueva_programacion and len(nueva_programacion) > len(ultima_programacion) * 0.5:
                ultima_programacion = nueva_programacion
                print(f"Iteración {i+1} completada - Longitud: {len(ultima_programacion)}")
            else:
                print(f"Iteración {i+1} descartada - Respuesta incompleta")
                break
        
        # Limpiar etiquetas HTML del contenido generado
        contenido_limpiado = limpiar_contenido_html(ultima_programacion)
        
        # Validar y corregir formato de tabla
        contenido_corregido = validar_y_corregir_formato_tabla(contenido_limpiado)
        
        # Limpieza final agresiva para asegurar que todo esté dentro de las celdas
        contenido_final = limpieza_final_tabla(contenido_corregido)
           
        return contenido_final
        
    except NoCredentialsError as e:
        error_msg = (
            "❌ Error: No se encontraron credenciales de AWS.\n\n"
            "Por favor, configura tus credenciales de una de las siguientes formas:\n\n"
            "1. Crear archivo .env en la raíz del proyecto con:\n"
            "   AWS_ACCESS_KEY_ID=tu_access_key\n"
            "   AWS_SECRET_ACCESS_KEY=tu_secret_key\n"
            "   AWS_REGION=us-east-1\n\n"
            "2. Configurar variables de entorno del sistema:\n"
            "   export AWS_ACCESS_KEY_ID=tu_access_key\n"
            "   export AWS_SECRET_ACCESS_KEY=tu_secret_key\n"
            "   export AWS_REGION=us-east-1\n\n"
            "3. Si usas Docker, asegúrate de que:\n"
            "   - El archivo .env existe en la raíz del proyecto\n"
            "   - docker-compose.yml tiene: env_file: - .env\n"
            "   - Las variables están en la sección environment\n"
            "   - Reconstruye el contenedor: docker-compose down && docker-compose up --build\n"
        )
        print(f"Error detallado: {error_msg}")
        return f"Error al generar la programación curricular: {error_msg}"
    except Exception as e:
        print(f"Error detallado: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"Error al generar la programación curricular: {e}"

def generar_imagen_promocional(prompt_imagen):
    """
    Genera una imagen promocional utilizando un modelo de difusión de Bedrock.
    """
    try:
        bedrock_runtime = crear_cliente_bedrock()
        prompt = f'''
        Generate a high-quality, professional educational image for a high school.
        The image should be visually appealing and focus on the prompt:
        '{prompt_imagen}'
        '''
        body = json.dumps({
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 10,
            "seed": 0,
            "steps": 50,
        })
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId='stability.stable-diffusion-xl-v1',
            accept='application/json',
            contentType='application/json'
        )
        response_body = json.loads(response.get('body').read())
        image_base64 = response_body.get('artifacts')[0].get('base64')
        return f"data:image/png;base64,{image_base64}"
    except NoCredentialsError as e:
        error_msg = (
            "❌ Error: No se encontraron credenciales de AWS.\n\n"
            "Por favor, configura tus credenciales de AWS en el archivo .env o como variables de entorno.\n"
        )
        return f"Error al generar la imagen: {error_msg}"
    except Exception as e:
        return f"Error al generar la imagen: {e}"

def generar_resumen_comentarios(comentarios):
    """
    Genera un resumen de comentarios de clientes utilizando un modelo de lenguaje de Bedrock.
    """
    try:
        bedrock_runtime = crear_cliente_bedrock()
        
        # Formato de prompt para Claude 3
        prompt = f"""Actúa como un especialista de educación, experto en calidad educativa. Lee los siguientes comentarios de estudiantes sobre las sesiones y genera un resumen conciso que destaque las opiniones clave, tanto positivas como negativas.

--- Comentarios ---
{comentarios}
---

Resumen:"""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.5
        })

        response = bedrock_runtime.invoke_model(
            body=body,
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            accept='application/json',
            contentType='application/json'
        )

        response_body = json.loads(response.get('body').read())
        # Claude 3 devuelve la respuesta en content[0].text
        return response_body.get('content', [{}])[0].get('text', '')

    except NoCredentialsError as e:
        error_msg = (
            "❌ Error: No se encontraron credenciales de AWS.\n\n"
            "Por favor, configura tus credenciales de AWS en el archivo .env o como variables de entorno.\n"
        )
        return f"Error al generar el resumen: {error_msg}"
    except Exception as e:
        return f"Error al generar el resumen: {e}"

def generar_unidad_didactica(area_curricular, grado, competencia_referencia=None):
    """
    Genera una unidad didáctica completa para un área curricular específica
    utilizando un modelo de lenguaje de Bedrock.
    
    Args:
        area_curricular: Área curricular (ej: Ciencia y Tecnología, Matemática, Comunicación)
        grado: Grado del nivel educativo (ej: 3, 4, 5)
        competencia_referencia: Competencia del Currículo Nacional a usar como referencia (opcional)
    """
    try:
        bedrock_runtime = crear_cliente_bedrock()
       
        # Construir contexto de competencia si se proporciona
        contexto_competencia = ""
        if competencia_referencia and competencia_referencia.strip():
            contexto_competencia = f"""

COMPETENCIA DE REFERENCIA DEL CURRÍCULO NACIONAL:
{competencia_referencia}

Esta competencia debe ser considerada y alineada en la unidad didáctica. Asegúrate de que los desempeños, capacidades y criterios de evaluación estén relacionados con esta competencia.
"""
        
        prompt = f"""
Actúa como especialista en diseño curricular. Tu tarea es crear una unidad didáctica completa para el área de {area_curricular} del grado {grado} de SECUNDARIA.
{contexto_competencia}
CRÍTICO: Debes generar SOLO una tabla con formato estricto. TODO el contenido debe estar DENTRO de las celdas de la tabla. NO generes nada fuera de la estructura de tabla. NO agregues texto antes o después de la tabla.

TU RESPUESTA DEBE COMENZAR EXACTAMENTE CON: | ITEM | CONTENIDO |
Y TERMINAR CON LA ÚLTIMA FILA DE LA TABLA. NADA MÁS.

CRÍTICO SOBRE EL ORDEN DE COLUMNAS:
- ITEM debe estar SIEMPRE a la IZQUIERDA (primera columna)
- CONTENIDO debe estar SIEMPRE a la DERECHA (segunda columna)
- NUNCA inviertas este orden: | CONTENIDO | ITEM | está INCORRECTO
- El formato correcto es: | ITEM | CONTENIDO |

FORMATO EXACTO REQUERIDO - Copia este formato exactamente (sin agregar nada antes o después):

| ITEM | CONTENIDO |
|------|-----------|
| **TÍTULO DE LA UNIDAD DIDÁCTICA** | Título completo aquí |
| **SITUACIÓN SIGNIFICATIVA** | Contexto real completo aquí. Todo el párrafo dentro de esta celda. |
| **COMPETENCIAS TRANSVERSALES** | Se desenvuelve en entornos virtuales: Estándar: [texto completo del estándar]. Instrumento: [texto completo del instrumento]. Gestiona su aprendizaje de manera autónoma: Estándar: [texto completo del estándar]. Instrumento: [texto completo del instrumento]. TODO dentro de esta misma celda, usando saltos de línea para separar competencias. Solo texto plano, sin viñetas. |
| **COMPETENCIAS DE ÁREA, CAPACIDADES Y DESEMPEÑOS PRECISADOS** | Competencia: [texto]. Capacidades: [capacidad 1], [capacidad 2]. Desempeños: Desempeño 1: [descripción completa con características]. Desempeño 2: [descripción completa]. TODO dentro de esta misma celda. Solo texto plano, sin viñetas ni listas con guiones. |
| **EVIDENCIAS DE APRENDIZAJE** | Evidencia 1: [descripción completa]
Evidencia 2: [descripción completa]
Todo dentro de esta celda. |
| **INSTRUMENTOS DE EVALUACIÓN** | Rúbrica: [contenido completo de la rúbrica con todos los niveles]
Lista de cotejo: [contenido completo]
Todo dentro de esta celda. |
| **VALORES Y ENFOQUES TRANSVERSALES** | Valores: [lista completa]
Enfoques: [lista completa]
Todo dentro de esta celda. |
| **SECUENCIA DE SESIONES** | Sesión 1: [título, actividades, desempeños, tiempo, recursos]
Sesión 2: [título, actividades, desempeños, tiempo, recursos]
Todo dentro de esta celda. |

REGLAS ESTRICTAS DE FORMATO:
1. SOLO genera la tabla con el formato exacto mostrado arriba
2. Cada fila debe tener exactamente: | **NOMBRE ITEM** | [contenido] |
3. TODO el contenido debe estar dentro de las celdas de la derecha
4. NO generes títulos, subtítulos o contenido fuera de la tabla
5. NO uses etiquetas HTML (<br>, <p>, etc.)
6. NO uses viñetas (•, -, *, →, etc.) - SOLO texto plano
7. Para separar contenido dentro de una celda, usa saltos de línea reales o puntos y comas
8. Para subsecciones dentro de una celda, usa texto plano con saltos de línea, NO listas con viñetas
9. Si hay múltiples competencias transversales, todas deben estar en la MISMA celda, separadas por saltos de línea
10. NO generes tablas anidadas, solo usa texto con saltos de línea dentro de cada celda
11. El contenido debe ser completo y detallado, pero TODO dentro de la estructura de tabla
12. Usa solo texto plano, sin formato de listas, sin viñetas, sin guiones para listas

INSTRUCCIONES DE CONTENIDO:
- El contenido debe ser apropiado para {grado}° grado de educación básica (Perú)
- Basado en el Currículo Nacional de Educación Básica - MINEDU
- Lenguaje claro y profesional
- Para COMPETENCIAS TRANSVERSALES: Incluir estándares completos e instrumentos detallados para cada competencia, todo dentro de la misma celda
- Para DESEMPEÑOS: Entre 8-12 desempeños específicos, precisos y observables
- Para INSTRUMENTOS: Rúbricas completas con niveles de logro (Inicio, Proceso, Logrado, Destacado)
- Para SECUENCIA DE SESIONES: 4-6 sesiones con título, actividades, desempeños, tiempo y recursos

EJEMPLO DE FORMATO CORRECTO PARA COMPETENCIAS TRANSVERSALES (dentro de la celda, solo texto plano):
Se desenvuelve en entornos virtuales: Estándar: Utiliza responsablemente las tecnologías de la información y comunicación para interactuar en entornos virtuales. Instrumento: Lista de cotejo sobre el uso responsable de herramientas digitales.

Gestiona su aprendizaje de manera autónoma: Estándar: Monitorea y ajusta sus procesos de aprendizaje, utilizando estrategias que respondan a sus características y necesidades. Instrumento: Rúbrica para evaluar la autorregulación del aprendizaje.

Recuerda: TODO debe estar dentro de la estructura de tabla, nada fuera. NO uses viñetas, solo texto plano.
"""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "top_p": 0.9
        })
       
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        contenido_generado = response_body.get('content', [{}])[0].get('text', '')
        
        # Limpiar etiquetas HTML del contenido generado
        contenido_limpiado = limpiar_contenido_html(contenido_generado)
        
        # Validar y corregir formato de tabla
        contenido_corregido = validar_y_corregir_formato_tabla(contenido_limpiado)
        
        # Limpieza final agresiva para asegurar que todo esté dentro de las celdas
        contenido_final = limpieza_final_tabla(contenido_corregido)
        
        return contenido_final
        
    except NoCredentialsError as e:
        error_msg = (
            "❌ Error: No se encontraron credenciales de AWS.\n\n"
            "Por favor, configura tus credenciales de una de las siguientes formas:\n\n"
            "1. Crear archivo .env en la raíz del proyecto con:\n"
            "   AWS_ACCESS_KEY_ID=tu_access_key\n"
            "   AWS_SECRET_ACCESS_KEY=tu_secret_key\n"
            "   AWS_REGION=us-east-1\n\n"
            "2. Configurar variables de entorno del sistema:\n"
            "   export AWS_ACCESS_KEY_ID=tu_access_key\n"
            "   export AWS_SECRET_ACCESS_KEY=tu_secret_key\n"
            "   export AWS_REGION=us-east-1\n\n"
            "3. Si usas Docker, asegúrate de que:\n"
            "   - El archivo .env existe en la raíz del proyecto\n"
            "   - docker-compose.yml tiene: env_file: - .env\n"
            "   - Las variables están en la sección environment\n"
            "   - Reconstruye el contenedor: docker-compose down && docker-compose up --build\n"
        )
        print(f"Error detallado: {error_msg}")
        return f"Error al generar la unidad didáctica: {error_msg}"
    except Exception as e:
        print(f"Error detallado: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"Error al generar la unidad didáctica: {e}"

def generar_sesion_aprendizaje(titulo_unidad, titulo_sesion, nivel, grado, seccion, duracion):
    """
    Genera una sesión de aprendizaje completa utilizando un modelo de lenguaje de Bedrock.
    
    Args:
        titulo_unidad: Título de la unidad didáctica
        titulo_sesion: Título de la sesión de aprendizaje
        nivel: Nivel educativo (Inicial, Primaria, Secundaria)
        grado: Grado del nivel
        seccion: Sección del grado
        duracion: Duración de la sesión
    """
    try:
        bedrock_runtime = crear_cliente_bedrock()
       
        prompt = f"""
Actúa como especialista en diseño de sesiones de aprendizaje. Tu tarea es crear una sesión de aprendizaje completa y detallada.

INFORMACIÓN DE LA SESIÓN:
- Título de la Unidad: {titulo_unidad}
- Título de la Sesión: {titulo_sesion}
- Nivel: {nivel}
- Grado: {grado}
- Sección: {seccion}
- Duración: {duracion}

CRÍTICO: Debes generar SOLO una tabla con formato estricto. TODO el contenido debe estar DENTRO de las celdas de la tabla. NO generes nada fuera de la estructura de tabla. NO agregues texto antes o después de la tabla.

TU RESPUESTA DEBE COMENZAR EXACTAMENTE CON: | ITEM | CONTENIDO |
Y TERMINAR CON LA ÚLTIMA FILA DE LA TABLA. NADA MÁS.

CRÍTICO SOBRE EL ORDEN DE COLUMNAS:
- ITEM debe estar SIEMPRE a la IZQUIERDA (primera columna)
- CONTENIDO debe estar SIEMPRE a la DERECHA (segunda columna)
- NUNCA inviertas este orden: | CONTENIDO | ITEM | está INCORRECTO
- El formato correcto es: | ITEM | CONTENIDO |

FORMATO EXACTO REQUERIDO - Copia este formato exactamente (sin agregar nada antes o después):

| ITEM | CONTENIDO |
|------|-----------|
| **DATOS INFORMATIVOS** | Área curricular, Grado y sección: {grado}° {seccion}, Nivel: {nivel}, Duración: {duracion}, Fecha de aplicación |
| **SITUACIÓN SIGNIFICATIVA** | Contexto real y motivador completo aquí. Todo el párrafo dentro de esta celda. |
| **COMPETENCIAS, CAPACIDADES Y DESEMPEÑOS PRECISADOS** | Competencia: [texto]. Capacidades: [capacidad 1], [capacidad 2]. Desempeños: Desempeño 1: [descripción completa con características]. Desempeño 2: [descripción completa]. TODO dentro de esta misma celda. Solo texto plano, sin viñetas. |
| **CRITERIOS DE EVALUACIÓN** | Criterio 1: [descripción completa]. Criterio 2: [descripción completa]. Todo dentro de esta celda. Solo texto plano. |
| **EVIDENCIA DE APRENDIZAJE** | Descripción completa de la evidencia aquí. Todo dentro de esta celda. Solo texto plano. |
| **INSTRUMENTO DE EVALUACIÓN** | Rúbrica completa: [contenido completo con todos los niveles y descriptores]. O Lista de cotejo: [contenido completo con todos los indicadores]. Todo dentro de esta celda. Solo texto plano. |
| **SECUENCIA DIDÁCTICA** | A. MOMENTO DE INICIO (aproximadamente 20% del tiempo): Actividad 1: [descripción detallada]. Actividad 2: [descripción detallada]. Tiempo: [tiempo específico]. B. MOMENTO DE DESARROLLO (aproximadamente 60% del tiempo): Actividad 1: [descripción detallada]. Actividad 2: [descripción detallada]. Tiempo: [tiempo específico]. C. MOMENTO DE CIERRE (aproximadamente 20% del tiempo): Actividad 1: [descripción detallada]. Actividad 2: [descripción detallada]
- Tiempo: [tiempo específico]

TODO dentro de esta misma celda. |
| **MATERIALES Y RECURSOS** | Materiales para docente: [lista completa]
Materiales para estudiantes: [lista completa]
Recursos: [lista completa]
Todo dentro de esta celda. |
| **REFLEXIÓN SOBRE LA ACTIVIDAD** | Dificultades: [texto completo]
Mejoras: [texto completo]
Ajustes: [texto completo]
Todo dentro de esta celda. |

REGLAS ESTRICTAS DE FORMATO:
1. SOLO genera la tabla con el formato exacto mostrado arriba
2. Cada fila debe tener exactamente: | **NOMBRE ITEM** | [contenido] |
3. TODO el contenido debe estar dentro de las celdas de la derecha
4. NO generes títulos, subtítulos o contenido fuera de la tabla
5. NO uses etiquetas HTML (<br>, <p>, etc.)
6. NO uses viñetas (•, -, *, →, etc.) - SOLO texto plano
7. Para separar contenido dentro de una celda, usa saltos de línea reales o puntos y comas
8. Para subsecciones dentro de una celda, usa texto plano con saltos de línea, NO listas con viñetas
9. Para SECUENCIA DIDÁCTICA, todos los momentos (Inicio, Desarrollo, Cierre) deben estar en la MISMA celda, separados por saltos de línea
10. NO generes tablas anidadas, solo usa texto con saltos de línea dentro de cada celda
11. El contenido debe ser completo y detallado, pero TODO dentro de la estructura de tabla
12. Usa solo texto plano, sin formato de listas, sin viñetas, sin guiones para listas

INSTRUCCIONES DE CONTENIDO:
- La sesión debe ser apropiada para {nivel} - {grado}° grado, sección {seccion}
- Duración total: {duracion}
- Basada en el Currículo Nacional de Educación Básica - MINEDU Perú
- Las actividades deben ser claras, secuenciales y prácticas
- Incluir tiempos aproximados para cada momento de la secuencia didáctica
- Considerar el contexto sociocultural de los estudiantes
- Promover el aprendizaje activo y participativo
- Incluir estrategias de atención a la diversidad

EJEMPLO DE FORMATO CORRECTO PARA SECUENCIA DIDÁCTICA (dentro de la celda, solo texto plano):
A. MOMENTO DE INICIO (aproximadamente 20% del tiempo): Actividad 1: [descripción detallada]. Actividad 2: [descripción detallada]. Tiempo: [tiempo específico]. B. MOMENTO DE DESARROLLO (aproximadamente 60% del tiempo): Actividad 1: [descripción detallada]. Actividad 2: [descripción detallada]. Tiempo: [tiempo específico]. C. MOMENTO DE CIERRE (aproximadamente 20% del tiempo): Actividad 1: [descripción detallada]. Actividad 2: [descripción detallada]. Tiempo: [tiempo específico].

Recuerda: TODO debe estar dentro de la estructura de tabla, nada fuera. NO uses viñetas, solo texto plano.
"""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "top_p": 0.9
        })
       
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        contenido_generado = response_body.get('content', [{}])[0].get('text', '')
        
        # Limpiar etiquetas HTML del contenido generado
        contenido_limpiado = limpiar_contenido_html(contenido_generado)
        
        # Validar y corregir formato de tabla
        contenido_corregido = validar_y_corregir_formato_tabla(contenido_limpiado)
        
        # Limpieza final agresiva para asegurar que todo esté dentro de las celdas
        contenido_final = limpieza_final_tabla(contenido_corregido)
        
        return contenido_final
        
    except NoCredentialsError as e:
        error_msg = (
            "❌ Error: No se encontraron credenciales de AWS.\n\n"
            "Por favor, configura tus credenciales de una de las siguientes formas:\n\n"
            "1. Crear archivo .env en la raíz del proyecto con:\n"
            "   AWS_ACCESS_KEY_ID=tu_access_key\n"
            "   AWS_SECRET_ACCESS_KEY=tu_secret_key\n"
            "   AWS_REGION=us-east-1\n\n"
            "2. Configurar variables de entorno del sistema:\n"
            "   export AWS_ACCESS_KEY_ID=tu_access_key\n"
            "   export AWS_SECRET_ACCESS_KEY=tu_secret_key\n"
            "   export AWS_REGION=us-east-1\n\n"
            "3. Si usas Docker, asegúrate de que:\n"
            "   - El archivo .env existe en la raíz del proyecto\n"
            "   - docker-compose.yml tiene: env_file: - .env\n"
            "   - Las variables están en la sección environment\n"
            "   - Reconstruye el contenedor: docker-compose down && docker-compose up --build\n"
        )
        print(f"Error detallado: {error_msg}")
        return f"Error al generar la sesión de aprendizaje: {error_msg}"
    except Exception as e:
        print(f"Error detallado: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"Error al generar la sesión de aprendizaje: {e}"