import warnings
# Suprimir warnings de ScriptRunContext cuando se ejecuta en modo depuración
# Estos warnings son normales al usar debugger y no afectan la funcionalidad
warnings.filterwarnings('ignore', message='.*ScriptRunContext.*')
warnings.filterwarnings('ignore', message='.*missing ScriptRunContext.*')

import streamlit as st
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from io import BytesIO

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configurar AWS_REGION si no está definido (valor por defecto)
if 'AWS_REGION' not in os.environ:
    os.environ['AWS_REGION'] = 'us-east-1'

# Configurar página ANTES que cualquier otra cosa
st.set_page_config(page_title="Generador Educativo AI", page_icon="🤖", layout="wide")

# Inicializar variables de estado
DOCX_OK = False
SERVICES_OK = False

# Título principal
st.title("Generador de contenido educativo AI 🤖")
st.markdown("Genera material educativo con exportación a Word")

# Verificar imports paso a paso
with st.spinner("🔄 Verificando dependencias..."):
    # Agregar path
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    except Exception as e:
        st.error(f"❌ Error agregando path: {e}")

    # Verificar python-docx
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_ALIGN_VERTICAL
        from docx.shared import Inches, Pt
        DOCX_OK = True
    except ImportError as e:
        st.error(f"❌ python-docx no disponible: {e}")
        DOCX_OK = False

    # Verificar servicios Bedrock
    try:
        from core.bedrock_services import (
            generar_unidad_didactica, 
            generar_sesion_aprendizaje,
            extraer_titulo_unidad_didactica,
            extraer_titulos_sesiones_unidad
        )
        SERVICES_OK = True
    except Exception as e:
        st.error(f"❌ Error importando servicios: {e}")
        SERVICES_OK = False
    
    # Importar competencias (opcional, no crítico si falla)
    COMPETENCIAS_DISPONIBLES = False
    try:
        from core.competencias_curriculares import (
            obtener_todas_las_competencias,
            obtener_competencias_por_area,
            formatear_competencia_para_tabla
        )
        COMPETENCIAS_DISPONIBLES = True
    except Exception:
        # Si falla la importación, simplemente no mostrar el selector de competencias
        COMPETENCIAS_DISPONIBLES = False

def normalizar_tabla_para_streamlit(contenido):
    """
    Normaliza el contenido de tabla para asegurar que siempre tenga formato ITEM | CONTENIDO
    y se muestre correctamente en Streamlit.
    
    Args:
        contenido: Contenido con tablas en formato markdown
        
    Returns:
        Contenido normalizado con tablas correctamente formateadas
    """
    if not contenido:
        return contenido
    
    lineas = contenido.split('\n')
    lineas_normalizadas = []
    dentro_tabla = False
    
    def es_item_valido(texto):
        """Determina si un texto es un ITEM válido"""
        if not texto or len(texto) > 100:
            return False
        texto_upper = texto.upper()
        palabras_item = ['TÍTULO', 'SITUACIÓN', 'COMPETENCIA', 'CAPACIDAD', 
                        'EVIDENCIA', 'INSTRUMENTO', 'VALOR', 'SECUENCIA', 
                        'ENFOQUE', 'SESIÓN', 'MATERIAL', 'REFLEXIÓN', 'ESTÁNDAR',
                        'DESEMPEÑO', 'PROPÓSITO', 'ORGANIZACIÓN', 'EVALUACIÓN']
        return (
            (len(texto) < 50 and texto.isupper()) or
            texto.startswith('**') or
            any(palabra in texto_upper for palabra in palabras_item)
        )
    
    def obtener_ultima_fila_info():
        """Obtiene información de la última fila de tabla"""
        if not lineas_normalizadas or not lineas_normalizadas[-1].startswith('|'):
            return None, None, None
        ultima = lineas_normalizadas[-1]
        partes = ultima.split('|')
        if len(partes) >= 3:
            item = partes[1].strip()
            contenido = partes[2].strip()
            return item, contenido, ultima
        elif len(partes) >= 2:
            item = partes[1].strip()
            return item, "", ultima
        return None, None, None
    
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        linea_stripped = linea.strip()
        
        # Detectar inicio de tabla
        if re.match(r'^\s*\|.*\|\s*$', linea_stripped) and linea_stripped.count('|') >= 2:
            dentro_tabla = True
            es_separador = re.match(r'^\s*\|[\s\-\:]+\|\s*$', linea_stripped)
            
            if es_separador:
                # Línea separadora, mantenerla
                lineas_normalizadas.append(linea_stripped)
            else:
                # Fila de tabla: normalizar a formato ITEM | CONTENIDO
                partes = linea.split('|')
                fila = [celda.strip() for celda in partes]
                # Eliminar celdas vacías al inicio y final
                while fila and not fila[0]:
                    fila.pop(0)
                while fila and not fila[-1]:
                    fila.pop()
                
                # Normalizar a 2 columnas
                if len(fila) == 0:
                    pass  # Fila vacía, saltar
                elif len(fila) == 1:
                    # Una columna: determinar si es ITEM o CONTENIDO
                    contenido_unico = fila[0]
                    es_item = es_item_valido(contenido_unico)
                    
                    # PRIMERO: Verificar si la última fila tiene ITEM sin CONTENIDO
                    item_ultimo, contenido_ultimo, ultima_linea = obtener_ultima_fila_info()
                    if item_ultimo and (not contenido_ultimo or len(contenido_ultimo) < 30):
                        # La última fila tiene ITEM sin CONTENIDO, agregar este contenido ahí
                        if contenido_ultimo:
                            lineas_normalizadas[-1] = f"| {item_ultimo} | {contenido_ultimo}\n{contenido_unico} |"
                        else:
                            lineas_normalizadas[-1] = f"| {item_ultimo} | {contenido_unico} |"
                    elif es_item:
                        # Es un ITEM nuevo
                        lineas_normalizadas.append(f"| {contenido_unico} | |")
                    else:
                        # Es CONTENIDO pero no hay ITEM previo sin CONTENIDO
                        lineas_normalizadas.append(f"| | {contenido_unico} |")
                elif len(fila) >= 2:
                    # Dos o más columnas: tomar ITEM y unir el resto como CONTENIDO
                    item = fila[0]
                    contenido = ' '.join([c for c in fila[1:] if c])
                    lineas_normalizadas.append(f"| {item} | {contenido} |")
        else:
            # Línea fuera de tabla (sin formato |)
            if dentro_tabla and linea_stripped:
                # Si estamos dentro de una tabla y encontramos contenido sin |,
                # SIEMPRE agregarlo a la última fila como CONTENIDO
                if (lineas_normalizadas and 
                    lineas_normalizadas[-1].startswith('|') and
                    not linea_stripped.startswith('#') and
                    not re.match(r'^\s*\|[\s\-\:]+\|\s*$', linea_stripped)):
                    item_ultimo, contenido_ultimo, ultima_linea = obtener_ultima_fila_info()
                    if item_ultimo is not None:
                        # Agregar a CONTENIDO de la última fila
                        if contenido_ultimo:
                            contenido_ultimo += '\n' + linea_stripped
                        else:
                            contenido_ultimo = linea_stripped
                        lineas_normalizadas[-1] = f"| {item_ultimo} | {contenido_ultimo} |"
                    else:
                        dentro_tabla = False
                        lineas_normalizadas.append(linea)
                else:
                    dentro_tabla = False
                    lineas_normalizadas.append(linea)
            else:
                lineas_normalizadas.append(linea)
        
        i += 1
    
    return '\n'.join(lineas_normalizadas)

# Función para procesar y formatear el contenido de unidad didáctica
def formatear_unidad_didactica(contenido_raw, area_curricular):
    """
    Procesa el contenido generado y lo estructura como una unidad didáctica profesional
    """
    # Normalizar las tablas antes de formatear
    contenido_normalizado = normalizar_tabla_para_streamlit(contenido_raw)
    
    contenido_formateado = f"""
# 📚 UNIDAD DIDÁCTICA

## 📋 ÁREA CURRICULAR: {area_curricular}

---

### 📅 INFORMACIÓN GENERAL
- **Área Curricular:** {area_curricular}
- **Fecha de Elaboración:** {datetime.now().strftime('%d de %B de %Y')}
- **Documento generado por:** IA Educativa

---

### 📖 CONTENIDO DE LA UNIDAD DIDÁCTICA

{contenido_normalizado}

---

### 📝 NOTAS METODOLÓGICAS

Esta unidad didáctica ha sido diseñada siguiendo los lineamientos del Currículo Nacional de la Educación Básica del Perú.

**Recomendaciones de implementación:**
- Considerar el contexto sociocultural de los estudiantes
- Adaptar las estrategias según los ritmos de aprendizaje
- Integrar recursos tecnológicos disponibles
- Promover el aprendizaje colaborativo

---

*Documento generado automáticamente por el Sistema de IA Educativa*
"""
    return contenido_formateado

# Función para procesar y formatear el contenido de sesión de aprendizaje
def formatear_sesion_aprendizaje(contenido_raw, titulo_unidad, titulo_sesion, nivel, grado, seccion, duracion):
    """
    Procesa el contenido generado y lo estructura como una sesión de aprendizaje profesional
    """
    # Normalizar las tablas antes de formatear
    contenido_normalizado = normalizar_tabla_para_streamlit(contenido_raw)
    
    contenido_formateado = f"""
# 📖 SESIÓN DE APRENDIZAJE

## 📚 {titulo_unidad}

### 🎯 {titulo_sesion}

---

### 📋 INFORMACIÓN GENERAL
- **Título de la Unidad:** {titulo_unidad}
- **Título de la Sesión:** {titulo_sesion}
- **Nivel:** {nivel}
- **Grado:** {grado}
- **Sección:** {seccion}
- **Duración:** {duracion}
- **Fecha de Elaboración:** {datetime.now().strftime('%d de %B de %Y')}
- **Documento generado por:** IA Educativa

---

### 📖 CONTENIDO DE LA SESIÓN DE APRENDIZAJE

{contenido_normalizado}

---

### 📝 NOTAS METODOLÓGICAS

Esta sesión de aprendizaje ha sido diseñada siguiendo los lineamientos del Currículo Nacional de la Educación Básica del Perú.

**Recomendaciones de implementación:**
- Considerar el contexto sociocultural de los estudiantes
- Adaptar las estrategias según los ritmos de aprendizaje
- Integrar recursos tecnológicos disponibles
- Promover el aprendizaje colaborativo

---

*Documento generado automáticamente por el Sistema de IA Educativa*
"""
    return contenido_formateado

# Función para obtener la ruta del Desktop
def obtener_ruta_desktop():
    """Obtiene la ruta del directorio Desktop del usuario"""
    # Si estamos en Docker, usar /app/outputs
    if os.path.exists("/app/outputs"):
        outputs_dir = Path("/app/outputs")
        outputs_dir.mkdir(parents=True, exist_ok=True)
        return outputs_dir
    
    # Si existe /app/desktop_outputs (montado desde Docker), usarlo
    if os.path.exists("/app/desktop_outputs"):
        outputs_dir = Path("/app/desktop_outputs")
        outputs_dir.mkdir(parents=True, exist_ok=True)
        return outputs_dir
    
    # Caso normal: usar Desktop del usuario
    home = Path.home()
    desktop = home / "Desktop"
    # Crear carpeta de outputs si no existe
    outputs_dir = desktop / "content_edu_outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    return outputs_dir

# Función para guardar archivo en Desktop
def guardar_archivo_desktop(contenido, nombre_archivo, es_bytes=False):
    """
    Guarda un archivo en el Desktop del usuario
    Args:
        contenido: Contenido del archivo (str o bytes)
        nombre_archivo: Nombre del archivo
        es_bytes: True si el contenido es bytes (para DOCX), False si es texto
    Returns:
        Ruta completa del archivo guardado
    """
    try:
        desktop_dir = obtener_ruta_desktop()
        ruta_completa = desktop_dir / nombre_archivo
        
        if es_bytes:
            with open(ruta_completa, 'wb') as f:
                f.write(contenido)
        else:
            with open(ruta_completa, 'w', encoding='utf-8') as f:
                f.write(contenido)
        
        return str(ruta_completa)
    except Exception as e:
        print(f"Error guardando archivo en Desktop: {e}")
        return None

def procesar_contenido_celda_tabla(celda, celda_word):
    """
    Procesa el contenido de una celda de tabla y formatea correctamente las viñetas y listas.
    
    Args:
        celda: Contenido de la celda como string (puede tener múltiples líneas y viñetas)
        celda_word: Objeto de celda de Word donde se insertará el contenido
    """
    if not celda or not celda.strip():
        return
    
    # Limpiar el texto primero (remover markdown bold)
    celda = celda.replace('**', '').strip()
    
    # Dividir por líneas
    lineas = celda.split('\n')
    
    # Limpiar la celda primero (eliminar el párrafo por defecto)
    if len(celda_word.paragraphs) > 0:
        celda_word.paragraphs[0].clear()
    else:
        celda_word.add_paragraph()
    
    # Procesar cada línea
    for idx, linea in enumerate(lineas):
        linea_original = linea
        linea = linea.strip()
        
        if not linea:
            # Si la línea está vacía, agregar un párrafo vacío solo si hay más líneas después
            if idx < len(lineas) - 1:
                celda_word.add_paragraph()
            continue
        
        # Detectar si es una viñeta
        es_viñeta = False
        texto_viñeta = linea
        
        # Verificar diferentes tipos de viñetas
        # Patrón 1: Viñetas comunes al inicio (•, -, *, →, ▪, ▫, ○, ●) con o sin espacios
        if re.match(r'^[\s]*[•\-\*→▪▫○●][\s]*', linea):
            es_viñeta = True
            # Remover el carácter de viñeta y espacios iniciales
            texto_viñeta = re.sub(r'^[\s]*[•\-\*→▪▫○●][\s]*', '', linea).strip()
        # Patrón 2: Lista numerada (1. , 1) , 1- )
        elif re.match(r'^[\s]*\d+[\.\)\-][\s]+', linea):
            es_viñeta = True
            # Mantener el número pero limpiar espacios extra al inicio
            texto_viñeta = re.sub(r'^[\s]+', '', linea)
        # Patrón 3: Viñetas simples sin espacio (solo el carácter)
        elif len(linea) > 1 and linea[0] in ['•', '-', '*', '→', '▪', '▫', '○', '●']:
            es_viñeta = True
            texto_viñeta = linea[1:].strip()
        
        # Crear o usar párrafo en la celda
        if idx == 0 and len(celda_word.paragraphs) > 0:
            # Usar el primer párrafo (ya existe después de clear)
            para = celda_word.paragraphs[0]
        else:
            # Crear nuevo párrafo
            para = celda_word.add_paragraph()
        
        # Si es viñeta, aplicar estilo de lista
        if es_viñeta and texto_viñeta:
            para.style = 'List Bullet'
            para.add_run(texto_viñeta)
        elif texto_viñeta:
            # Texto normal
            para.add_run(texto_viñeta)

# Función mejorada para crear Word
def crear_documento_profesional(contenido, titulo, subtitulo_extra=""):
    if not DOCX_OK:
        return None
    
    doc = Document()
    
    # Configurar propiedades del documento
    doc.core_properties.title = titulo
    doc.core_properties.author = "Sistema IA Educativa"
    doc.core_properties.subject = titulo
    
    # Título principal
    titulo_principal = doc.add_heading(titulo.upper(), 0)
    titulo_principal.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Subtítulo si existe
    if subtitulo_extra:
        subtitulo = doc.add_heading(subtitulo_extra, 1)
        subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Información del documento
    info_para = doc.add_paragraph()
    info_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    info_run = info_para.add_run(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}\nGenerado por: IA Educativa")
    info_run.italic = True
    
    # Línea separadora
    doc.add_paragraph("=" * 80)
    
    # Procesar contenido línea por línea con formato mejorado
    lineas = contenido.split('\n')
    i = 0
    while i < len(lineas):
        line = lineas[i].strip()
        if not line:
            i += 1
            continue
        
        # Detectar tablas (líneas que empiezan y terminan con | - formato markdown completo)
        # PRIORIDAD: Si tiene | al inicio y final, es una tabla
        if re.match(r'^\s*\|.*\|\s*$', line) and line.count('|') >= 2:
            # Intentar crear una tabla real
            filas_tabla = []
            j = i
            dentro_tabla = True
            ultima_fila_completa = None
            
            # Recopilar líneas consecutivas que parecen ser parte de una tabla
            while j < len(lineas) and dentro_tabla:
                current_line = lineas[j]
                current_line_stripped = current_line.strip()
                
                # Si la línea tiene | y empieza y termina con |, es parte de la tabla (formato markdown completo)
                if re.match(r'^\s*\|.*\|\s*$', current_line_stripped) and current_line_stripped.count('|') >= 2:
                    # Verificar si es una línea separadora de markdown (solo contiene |, -, :, espacios)
                    es_separador = re.match(r'^\s*\|[\s\-\:]+\|\s*$', current_line_stripped)
                    if not es_separador:
                        # Dividir por | y filtrar celdas vacías al inicio y final
                        partes = current_line.split('|')
                        # Limpiar cada celda
                        fila = [celda.strip() for celda in partes]
                        # Eliminar celdas vacías al inicio y final (formato markdown)
                        while fila and not fila[0]:
                            fila.pop(0)
                        while fila and not fila[-1]:
                            fila.pop()
                        
                        # Validar y corregir el formato: debe tener exactamente 2 columnas [ITEM, CONTENIDO]
                        if len(fila) == 0:
                            # Fila vacía, saltar
                            pass
                        elif len(fila) == 1:
                            # Solo una columna: verificar si es un ITEM o CONTENIDO
                            contenido_unico = fila[0]
                            
                            # CRITERIOS MÁS ESTRICTOS PARA DETECTAR ITEM
                            es_item = False
                            contenido_len = len(contenido_unico)
                            
                            # Si es muy largo (> 100 caracteres), definitivamente es CONTENIDO
                            if contenido_len > 100:
                                es_item = False
                            # Si es corto y está en mayúsculas, probablemente es ITEM
                            elif contenido_len < 50 and contenido_unico.isupper():
                                es_item = True
                            # Si empieza con ** y es corto, es ITEM
                            elif contenido_unico.startswith('**') and contenido_len < 80:
                                es_item = True
                            # Si contiene palabras clave de ITEMs y es corto
                            elif contenido_len < 80:
                                palabras_item = ['TÍTULO', 'SITUACIÓN', 'COMPETENCIA', 'CAPACIDAD', 
                                                'EVIDENCIA', 'INSTRUMENTO', 'VALOR', 'SECUENCIA', 
                                                'ENFOQUE', 'SESIÓN', 'MATERIAL', 'REFLEXIÓN', 'ESTÁNDAR',
                                                'DESEMPEÑO', 'PROPÓSITO', 'ORGANIZACIÓN', 'EVALUACIÓN']
                                contenido_upper = contenido_unico.upper()
                                tiene_palabra_clave = any(
                                    contenido_upper.startswith(palabra) or 
                                    f' {palabra}' in contenido_upper or
                                    f'{palabra} ' in contenido_upper
                                    for palabra in palabras_item
                                )
                                if tiene_palabra_clave:
                                    es_item = True
                            
                            # Si la última fila tenía ITEM sin CONTENIDO, este contenido debe ir a CONTENIDO
                            if (len(filas_tabla) > 0 and 
                                len(filas_tabla[-1]) >= 1 and 
                                filas_tabla[-1][0] and 
                                not filas_tabla[-1][1]):
                                # Agregar este contenido a CONTENIDO de la última fila
                                filas_tabla[-1][1] = contenido_unico
                                ultima_fila_completa = len(filas_tabla) - 1
                            elif es_item:
                                # Es un ITEM, agregar como [ITEM, ""]
                                filas_tabla.append([contenido_unico, ""])
                                ultima_fila_completa = len(filas_tabla) - 1
                            else:
                                # Es CONTENIDO, agregar como ["", CONTENIDO] o a la última fila si tenía ITEM
                                if (len(filas_tabla) > 0 and 
                                    len(filas_tabla[-1]) >= 1 and 
                                    filas_tabla[-1][0] and 
                                    not filas_tabla[-1][1]):
                                    filas_tabla[-1][1] = contenido_unico
                                    ultima_fila_completa = len(filas_tabla) - 1
                                else:
                                    filas_tabla.append(["", contenido_unico])
                                    ultima_fila_completa = len(filas_tabla) - 1
                        elif len(fila) >= 2:
                            # Tiene 2 o más columnas: tomar solo las primeras 2 [ITEM, CONTENIDO]
                            item = fila[0].strip()
                            contenido = ' '.join(fila[1:]).strip()  # Unir todas las columnas adicionales en contenido
                            filas_tabla.append([item, contenido])
                            ultima_fila_completa = len(filas_tabla) - 1
                else:
                    # Línea sin | - puede ser contenido multilínea dentro de la última celda
                    # Solo agregar si:
                    # 1. Ya tenemos al menos una fila de tabla
                    # 2. La línea no está vacía
                    # 3. La línea no es claramente el inicio de otra sección (encabezado, lista, etc.)
                    if (len(filas_tabla) > 0 and 
                        current_line_stripped and 
                        not current_line_stripped.startswith('#') and
                        not current_line_stripped.startswith(('•', '-', '*', '→')) and
                        (not current_line_stripped.isupper() or len(current_line_stripped) < 5)):
                        # Agregar este contenido a la última celda de la última fila (columna CONTENIDO = índice 1)
                        if ultima_fila_completa is not None and len(filas_tabla[ultima_fila_completa]) >= 1:
                            # Asegurar que la fila tenga al menos 2 columnas
                            while len(filas_tabla[ultima_fila_completa]) < 2:
                                filas_tabla[ultima_fila_completa].append("")
                            # Agregar a la columna CONTENIDO (índice 1, segunda columna)
                            contenido_actual = filas_tabla[ultima_fila_completa][1] if len(filas_tabla[ultima_fila_completa]) > 1 else ""
                            if contenido_actual:
                                filas_tabla[ultima_fila_completa][1] = contenido_actual + '\n' + current_line_stripped
                            else:
                                filas_tabla[ultima_fila_completa][1] = current_line_stripped
                    else:
                        # Esta línea claramente no es parte de la tabla
                        dentro_tabla = False
                        break
                j += 1
            
            # Si tenemos al menos 1 fila (puede ser solo encabezado), crear tabla
            if len(filas_tabla) >= 1:
                # Validar y normalizar: todas las filas deben tener exactamente 2 columnas (ITEM | CONTENIDO)
                num_cols = 2  # Forzar 2 columnas
                
                # Asegurar que todas las filas tengan exactamente 2 columnas [ITEM, CONTENIDO]
                filas_normalizadas = []
                for fila in filas_tabla:
                    # Normalizar a exactamente 2 columnas
                    if len(fila) == 0:
                        # Fila vacía, crear fila con dos celdas vacías
                        fila_normalizada = ["", ""]
                    elif len(fila) == 1:
                        # Solo una columna: determinar si es ITEM o CONTENIDO
                        contenido_unico = fila[0].strip()
                        # Detectar si es un ITEM (títulos comunes en mayúsculas o con **)
                        es_item = (
                            contenido_unico.isupper() or
                            contenido_unico.startswith('**') or
                            contenido_unico.startswith('*') or
                            (len(contenido_unico) < 60 and any(
                                palabra in contenido_unico.upper() 
                                for palabra in ['TÍTULO', 'SITUACIÓN', 'COMPETENCIA', 'CAPACIDAD', 
                                               'EVIDENCIA', 'INSTRUMENTO', 'VALOR', 'SECUENCIA', 
                                               'ENFOQUE', 'SESIÓN', 'MATERIAL', 'REFLEXIÓN']
                            ))
                        )
                        if es_item:
                            # Es un ITEM, colocar en columna izquierda
                            fila_normalizada = [contenido_unico, ""]
                        else:
                            # Es CONTENIDO, colocar en columna derecha (solo si la última fila tenía ITEM)
                            # Si la última fila normalizada tenía ITEM pero no CONTENIDO, agregar aquí
                            if filas_normalizadas and filas_normalizadas[-1][0] and not filas_normalizadas[-1][1]:
                                filas_normalizadas[-1][1] = contenido_unico
                                continue  # Ya se agregó a la fila anterior
                            else:
                                # Nueva fila con ITEM vacío y CONTENIDO
                                fila_normalizada = ["", contenido_unico]
                    elif len(fila) >= 2:
                        # Tiene 2 o más columnas: [ITEM, CONTENIDO]
                        item = fila[0].strip()
                        # Unir todas las columnas adicionales en CONTENIDO
                        contenido = ' '.join([c.strip() for c in fila[1:] if c.strip()]).strip()
                        fila_normalizada = [item, contenido]
                    else:
                        # Caso por defecto: dos celdas vacías
                        fila_normalizada = ["", ""]
                    
                    # Asegurar que siempre tenga exactamente 2 columnas
                    while len(fila_normalizada) < 2:
                        fila_normalizada.append("")
                    fila_normalizada = fila_normalizada[:2]  # Tomar solo las primeras 2
                    filas_normalizadas.append(fila_normalizada)
                
                # Crear tabla en Word
                tabla = doc.add_table(rows=len(filas_normalizadas), cols=num_cols)
                tabla.style = 'Light Grid Accent 1'
                
                # Configurar ancho de columnas (primera columna más estrecha para ITEM, segunda más ancha para CONTENIDO)
                if len(tabla.columns) >= 2:
                    tabla.columns[0].width = Inches(1.5)  # Columna ITEM: 1.5 pulgadas
                    tabla.columns[1].width = Inches(5.5)  # Columna CONTENIDO: 5.5 pulgadas
                
                # Llenar la tabla
                for row_idx, fila in enumerate(filas_normalizadas):
                    # Asegurar que siempre tengamos exactamente 2 columnas: [ITEM, CONTENIDO]
                    item_texto = fila[0] if len(fila) > 0 else ""
                    contenido_texto = fila[1] if len(fila) > 1 else ""
                    
                    # Columna 0: ITEM (izquierda)
                    celda_item = tabla.rows[row_idx].cells[0]
                    celda_item.vertical_alignment = WD_ALIGN_VERTICAL.TOP
                    procesar_contenido_celda_tabla(item_texto, celda_item)
                    for paragraph in celda_item.paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    
                    # Columna 1: CONTENIDO (derecha)
                    celda_contenido = tabla.rows[row_idx].cells[1]
                    celda_contenido.vertical_alignment = WD_ALIGN_VERTICAL.TOP
                    procesar_contenido_celda_tabla(contenido_texto, celda_contenido)
                    for paragraph in celda_contenido.paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    
                    # Hacer la primera fila en negrita (encabezados)
                    if row_idx == 0:
                        for paragraph in celda_item.paragraphs:
                            for run in paragraph.runs:
                                run.bold = True
                        for paragraph in celda_contenido.paragraphs:
                            for run in paragraph.runs:
                                run.bold = True
                
                i = j - 1  # Ajustar índice
            else:
                # Si no es una tabla válida, agregar como texto
                cleaned_line = line.replace('|', ' | ').strip()
                doc.add_paragraph(cleaned_line)
        
        # Detectar encabezados (solo si no es tabla)
        elif line.startswith('#'):
            level = line.count('#')
            text = line.replace('#', '').strip()
            if text:
                doc.add_heading(text, level=min(level, 3))
        
        # Detectar listas con bullets
        elif line.startswith(('•', '-', '*', '→')):
            para = doc.add_paragraph()
            para.style = 'List Bullet'
            para.add_run(line[1:].strip())
        
        # Detectar texto en mayúsculas (posibles títulos)
        elif line.isupper() and len(line) > 5 and not line.startswith(('COMPETENCIA', 'CAPACIDAD', 'CONTENIDO', 'DESEMPEÑO', 'CRITERIO', 'INSTRUMENTO')):
            doc.add_heading(line.title(), 2)
        
        # Detectar secciones importantes (COMPETENCIA, CAPACIDADES, etc.)
        elif any(palabra in line.upper() for palabra in ['COMPETENCIA', 'CAPACIDADES', 'CONTENIDOS', 'DESEMPEÑOS', 'CRITERIOS', 'INSTRUMENTOS', 'TRANSVERSALES', 'SESIONES']):
            if line.isupper() and len(line) > 5:
                doc.add_heading(line.title(), 2)
            else:
                doc.add_paragraph(line)
        
        # Texto normal
        else:
            if len(line) > 5:  # Agregar líneas con contenido significativo
                doc.add_paragraph(line)
        
        i += 1
    
    # Pie de página
    doc.add_page_break()
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run("GENERADO POR SISTEMA IA EDUCATIVA\nMinisterio de Educación - República del Perú")
    footer_run.italic = True
    
    # Convertir a bytes
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# Función específica para crear documento de sesión de aprendizaje
def crear_documento_sesion_aprendizaje(contenido, titulo_unidad, titulo_sesion, nivel, grado, seccion):
    """
    Crea un documento Word para sesión de aprendizaje con título de unidad y título de sesión.
    
    Args:
        contenido: Contenido de la sesión de aprendizaje
        titulo_unidad: Título de la unidad didáctica
        titulo_sesion: Título de la sesión de aprendizaje
        nivel: Nivel educativo
        grado: Grado
        seccion: Sección
    """
    if not DOCX_OK:
        return None
    
    doc = Document()
    
    # Configurar propiedades del documento
    doc.core_properties.title = f"Sesión de Aprendizaje: {titulo_sesion}"
    doc.core_properties.author = "Sistema IA Educativa"
    doc.core_properties.subject = f"Unidad: {titulo_unidad} - Sesión: {titulo_sesion}"
    
    # Título principal
    titulo_principal = doc.add_heading("SESIÓN DE APRENDIZAJE", 0)
    titulo_principal.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Título de la unidad
    if titulo_unidad:
        titulo_unidad_heading = doc.add_heading(f"Unidad: {titulo_unidad}", 1)
        titulo_unidad_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Título de la sesión
    if titulo_sesion:
        titulo_sesion_heading = doc.add_heading(f"Sesión: {titulo_sesion}", 2)
        titulo_sesion_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Información del documento
    info_para = doc.add_paragraph()
    info_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    info_text = f"Fecha: {datetime.now().strftime('%d/%m/%Y')}\n"
    info_text += f"Nivel: {nivel}\n"
    info_text += f"Grado: {grado}° - Sección: {seccion}\n"
    info_text += "Generado por: IA Educativa"
    info_run = info_para.add_run(info_text)
    info_run.italic = True
    
    # Línea separadora
    doc.add_paragraph("=" * 80)
    
    # Procesar contenido línea por línea (reutilizar lógica mejorada de crear_documento_profesional)
    lineas = contenido.split('\n')
    i = 0
    while i < len(lineas):
        line = lineas[i].strip()
        if not line:
            i += 1
            continue
        
        # Detectar tablas (líneas que empiezan y terminan con | - formato markdown completo)
        # PRIORIDAD: Si tiene | al inicio y final, es una tabla
        if re.match(r'^\s*\|.*\|\s*$', line) and line.count('|') >= 2:
            # Intentar crear una tabla real
            filas_tabla = []
            j = i
            dentro_tabla = True
            ultima_fila_completa = None
            
            # Recopilar líneas consecutivas que parecen ser parte de una tabla
            while j < len(lineas) and dentro_tabla:
                current_line = lineas[j]
                current_line_stripped = current_line.strip()
                
                # Si la línea tiene | y empieza y termina con |, es parte de la tabla (formato markdown completo)
                if re.match(r'^\s*\|.*\|\s*$', current_line_stripped) and current_line_stripped.count('|') >= 2:
                    # Verificar si es una línea separadora de markdown (solo contiene |, -, :, espacios)
                    es_separador = re.match(r'^\s*\|[\s\-\:]+\|\s*$', current_line_stripped)
                    if not es_separador:
                        # Dividir por | y filtrar celdas vacías al inicio y final
                        partes = current_line.split('|')
                        # Limpiar cada celda
                        fila = [celda.strip() for celda in partes]
                        # Eliminar celdas vacías al inicio y final (formato markdown)
                        while fila and not fila[0]:
                            fila.pop(0)
                        while fila and not fila[-1]:
                            fila.pop()
                        
                        # Validar y corregir el formato: debe tener exactamente 2 columnas [ITEM, CONTENIDO]
                        if len(fila) == 0:
                            # Fila vacía, saltar
                            pass
                        elif len(fila) == 1:
                            # Solo una columna: verificar si es un ITEM o CONTENIDO
                            contenido_unico = fila[0]
                            
                            # CRITERIOS MÁS ESTRICTOS PARA DETECTAR ITEM
                            es_item = False
                            contenido_len = len(contenido_unico)
                            
                            # Si es muy largo (> 100 caracteres), definitivamente es CONTENIDO
                            if contenido_len > 100:
                                es_item = False
                            # Si es corto y está en mayúsculas, probablemente es ITEM
                            elif contenido_len < 50 and contenido_unico.isupper():
                                es_item = True
                            # Si empieza con ** y es corto, es ITEM
                            elif contenido_unico.startswith('**') and contenido_len < 80:
                                es_item = True
                            # Si contiene palabras clave de ITEMs y es corto
                            elif contenido_len < 80:
                                palabras_item = ['TÍTULO', 'SITUACIÓN', 'COMPETENCIA', 'CAPACIDAD', 
                                                'EVIDENCIA', 'INSTRUMENTO', 'VALOR', 'SECUENCIA', 
                                                'ENFOQUE', 'SESIÓN', 'MATERIAL', 'REFLEXIÓN', 'ESTÁNDAR',
                                                'DESEMPEÑO', 'PROPÓSITO', 'ORGANIZACIÓN', 'EVALUACIÓN']
                                contenido_upper = contenido_unico.upper()
                                tiene_palabra_clave = any(
                                    contenido_upper.startswith(palabra) or 
                                    f' {palabra}' in contenido_upper or
                                    f'{palabra} ' in contenido_upper
                                    for palabra in palabras_item
                                )
                                if tiene_palabra_clave:
                                    es_item = True
                            
                            # Si la última fila tenía ITEM sin CONTENIDO, este contenido debe ir a CONTENIDO
                            if (len(filas_tabla) > 0 and 
                                len(filas_tabla[-1]) >= 1 and 
                                filas_tabla[-1][0] and 
                                not filas_tabla[-1][1]):
                                # Agregar este contenido a CONTENIDO de la última fila
                                filas_tabla[-1][1] = contenido_unico
                                ultima_fila_completa = len(filas_tabla) - 1
                            elif es_item:
                                # Es un ITEM, agregar como [ITEM, ""]
                                filas_tabla.append([contenido_unico, ""])
                                ultima_fila_completa = len(filas_tabla) - 1
                            else:
                                # Es CONTENIDO, agregar como ["", CONTENIDO] o a la última fila si tenía ITEM
                                if (len(filas_tabla) > 0 and 
                                    len(filas_tabla[-1]) >= 1 and 
                                    filas_tabla[-1][0] and 
                                    not filas_tabla[-1][1]):
                                    filas_tabla[-1][1] = contenido_unico
                                    ultima_fila_completa = len(filas_tabla) - 1
                                else:
                                    filas_tabla.append(["", contenido_unico])
                                    ultima_fila_completa = len(filas_tabla) - 1
                        elif len(fila) >= 2:
                            # Tiene 2 o más columnas: tomar solo las primeras 2 [ITEM, CONTENIDO]
                            item = fila[0].strip()
                            contenido = ' '.join(fila[1:]).strip()  # Unir todas las columnas adicionales en contenido
                            filas_tabla.append([item, contenido])
                            ultima_fila_completa = len(filas_tabla) - 1
                else:
                    # Línea sin | - puede ser contenido multilínea dentro de la última celda
                    # Solo agregar si:
                    # 1. Ya tenemos al menos una fila de tabla
                    # 2. La línea no está vacía
                    # 3. La línea no es claramente el inicio de otra sección (encabezado, lista, etc.)
                    if (len(filas_tabla) > 0 and 
                        current_line_stripped and 
                        not current_line_stripped.startswith('#') and
                        not current_line_stripped.startswith(('•', '-', '*', '→')) and
                        (not current_line_stripped.isupper() or len(current_line_stripped) < 5)):
                        # Agregar este contenido a la última celda de la última fila (columna CONTENIDO = índice 1)
                        if ultima_fila_completa is not None and len(filas_tabla[ultima_fila_completa]) >= 1:
                            # Asegurar que la fila tenga al menos 2 columnas
                            while len(filas_tabla[ultima_fila_completa]) < 2:
                                filas_tabla[ultima_fila_completa].append("")
                            # Agregar a la columna CONTENIDO (índice 1, segunda columna)
                            contenido_actual = filas_tabla[ultima_fila_completa][1] if len(filas_tabla[ultima_fila_completa]) > 1 else ""
                            if contenido_actual:
                                filas_tabla[ultima_fila_completa][1] = contenido_actual + '\n' + current_line_stripped
                            else:
                                filas_tabla[ultima_fila_completa][1] = current_line_stripped
                    else:
                        # Esta línea claramente no es parte de la tabla
                        dentro_tabla = False
                        break
                j += 1
            
            # Si tenemos al menos 1 fila (puede ser solo encabezado), crear tabla
            if len(filas_tabla) >= 1:
                # Validar y normalizar: todas las filas deben tener exactamente 2 columnas (ITEM | CONTENIDO)
                num_cols = 2  # Forzar 2 columnas
                
                # Asegurar que todas las filas tengan exactamente 2 columnas [ITEM, CONTENIDO]
                filas_normalizadas = []
                for fila in filas_tabla:
                    # Normalizar a exactamente 2 columnas
                    if len(fila) == 0:
                        # Fila vacía, crear fila con dos celdas vacías
                        fila_normalizada = ["", ""]
                    elif len(fila) == 1:
                        # Solo una columna: determinar si es ITEM o CONTENIDO
                        contenido_unico = fila[0].strip()
                        # Detectar si es un ITEM (títulos comunes en mayúsculas o con **)
                        es_item = (
                            contenido_unico.isupper() or
                            contenido_unico.startswith('**') or
                            contenido_unico.startswith('*') or
                            (len(contenido_unico) < 60 and any(
                                palabra in contenido_unico.upper() 
                                for palabra in ['TÍTULO', 'SITUACIÓN', 'COMPETENCIA', 'CAPACIDAD', 
                                               'EVIDENCIA', 'INSTRUMENTO', 'VALOR', 'SECUENCIA', 
                                               'ENFOQUE', 'SESIÓN', 'MATERIAL', 'REFLEXIÓN']
                            ))
                        )
                        if es_item:
                            # Es un ITEM, colocar en columna izquierda
                            fila_normalizada = [contenido_unico, ""]
                        else:
                            # Es CONTENIDO, colocar en columna derecha (solo si la última fila tenía ITEM)
                            # Si la última fila normalizada tenía ITEM pero no CONTENIDO, agregar aquí
                            if filas_normalizadas and filas_normalizadas[-1][0] and not filas_normalizadas[-1][1]:
                                filas_normalizadas[-1][1] = contenido_unico
                                continue  # Ya se agregó a la fila anterior
                            else:
                                # Nueva fila con ITEM vacío y CONTENIDO
                                fila_normalizada = ["", contenido_unico]
                    elif len(fila) >= 2:
                        # Tiene 2 o más columnas: [ITEM, CONTENIDO]
                        item = fila[0].strip()
                        # Unir todas las columnas adicionales en CONTENIDO
                        contenido = ' '.join([c.strip() for c in fila[1:] if c.strip()]).strip()
                        fila_normalizada = [item, contenido]
                    else:
                        # Caso por defecto: dos celdas vacías
                        fila_normalizada = ["", ""]
                    
                    # Asegurar que siempre tenga exactamente 2 columnas
                    while len(fila_normalizada) < 2:
                        fila_normalizada.append("")
                    fila_normalizada = fila_normalizada[:2]  # Tomar solo las primeras 2
                    filas_normalizadas.append(fila_normalizada)
                
                # Crear tabla en Word
                tabla = doc.add_table(rows=len(filas_normalizadas), cols=num_cols)
                tabla.style = 'Light Grid Accent 1'
                
                # Configurar ancho de columnas (primera columna más estrecha para ITEM, segunda más ancha para CONTENIDO)
                if len(tabla.columns) >= 2:
                    tabla.columns[0].width = Inches(1.5)  # Columna ITEM: 1.5 pulgadas
                    tabla.columns[1].width = Inches(5.5)  # Columna CONTENIDO: 5.5 pulgadas
                
                # Llenar la tabla
                for row_idx, fila in enumerate(filas_normalizadas):
                    # Asegurar que siempre tengamos exactamente 2 columnas: [ITEM, CONTENIDO]
                    item_texto = fila[0] if len(fila) > 0 else ""
                    contenido_texto = fila[1] if len(fila) > 1 else ""
                    
                    # Columna 0: ITEM (izquierda)
                    celda_item = tabla.rows[row_idx].cells[0]
                    celda_item.vertical_alignment = WD_ALIGN_VERTICAL.TOP
                    procesar_contenido_celda_tabla(item_texto, celda_item)
                    for paragraph in celda_item.paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    
                    # Columna 1: CONTENIDO (derecha)
                    celda_contenido = tabla.rows[row_idx].cells[1]
                    celda_contenido.vertical_alignment = WD_ALIGN_VERTICAL.TOP
                    procesar_contenido_celda_tabla(contenido_texto, celda_contenido)
                    for paragraph in celda_contenido.paragraphs:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    
                    # Hacer la primera fila en negrita (encabezados)
                    if row_idx == 0:
                        for paragraph in celda_item.paragraphs:
                            for run in paragraph.runs:
                                run.bold = True
                        for paragraph in celda_contenido.paragraphs:
                            for run in paragraph.runs:
                                run.bold = True
                
                i = j - 1  # Ajustar índice
            else:
                # Si no es una tabla válida, agregar como texto
                cleaned_line = line.replace('|', ' | ').strip()
                doc.add_paragraph(cleaned_line)
        
        # Detectar encabezados (solo si no es tabla)
        elif line.startswith('#'):
            level = line.count('#')
            text = line.replace('#', '').strip()
            if text:
                doc.add_heading(text, level=min(level, 3))
        
        # Detectar listas con bullets
        elif line.startswith(('•', '-', '*', '→')):
            para = doc.add_paragraph()
            para.style = 'List Bullet'
            para.add_run(line[1:].strip())
        
        # Detectar texto en mayúsculas (posibles títulos)
        elif line.isupper() and len(line) > 5 and not line.startswith(('COMPETENCIA', 'CAPACIDAD', 'CONTENIDO', 'DESEMPEÑO', 'CRITERIO', 'INSTRUMENTO')):
            doc.add_heading(line.title(), 2)
        
        # Detectar secciones importantes
        elif any(palabra in line.upper() for palabra in ['COMPETENCIA', 'CAPACIDADES', 'CONTENIDOS', 'DESEMPEÑOS', 'CRITERIOS', 'INSTRUMENTOS', 'TRANSVERSALES', 'SESIONES']):
            if line.isupper() and len(line) > 5:
                doc.add_heading(line.title(), 2)
            else:
                doc.add_paragraph(line)
        
        # Texto normal
        else:
            if len(line) > 5:  # Agregar líneas con contenido significativo
                doc.add_paragraph(line)
        
        i += 1
    
    # Pie de página
    doc.add_page_break()
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_text = f"GENERADO POR SISTEMA IA EDUCATIVA\n"
    footer_text += f"Unidad: {titulo_unidad}\n"
    footer_text += f"Sesión: {titulo_sesion}\n"
    footer_text += "Ministerio de Educación - República del Perú"
    footer_run = footer.add_run(footer_text)
    footer_run.italic = True
    
    # Convertir a bytes
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# Solo mostrar tabs si todo está OK
if SERVICES_OK:
    st.success("🎉 ¡Sistema listo! Genera tu contenido educativo.")
    
    # Crear tabs
    tab1, tab2 = st.tabs(["📚 Unidad Didáctica", "📖 Sesión de Aprendizaje"])
    
    with tab1:
        st.header("📚 Generador de Unidad Didáctica")
        
        # Información contextual
        with st.expander("ℹ️ Información sobre la Unidad Didáctica"):
            st.markdown("""
            **¿Qué incluye una unidad didáctica?**
            - ✅ Competencias y capacidades específicas
            - ✅ Contenidos organizados por temas
            - ✅ Desempeños observables y medibles
            - ✅ Criterios e instrumentos de evaluación
            - ✅ Estrategias metodológicas
            
            **Basado en:** Currículo Nacional de Educación Básica - MINEDU Perú
            """)
        
        with st.form("form_unidad", clear_on_submit=False):
            area_curricular = st.text_input(
                "📚 Área Curricular",
                placeholder="Ej: Ciencia y Tecnología, Matemática, Comunicación, etc.",
                help="Ingresa el área curricular para la unidad didáctica"
            )
            
            # Selector de competencias (opcional, solo si está disponible)
            competencia_seleccionada = ""
            if COMPETENCIAS_DISPONIBLES:
                try:
                    competencias_relacionadas = []
                    if area_curricular and area_curricular.strip():
                        competencias_relacionadas = obtener_competencias_por_area(area_curricular.strip())
                    
                    if competencias_relacionadas:
                        st.info(f"📋 Se encontraron {len(competencias_relacionadas)} competencias relacionadas con '{area_curricular}':")
                        competencias_opciones = [formatear_competencia_para_tabla(comp) for comp in competencias_relacionadas]
                        competencia_seleccionada = st.selectbox(
                            "🎯 Competencia (opcional - se usará como referencia)",
                            options=[""] + competencias_opciones,
                            help="Selecciona una competencia relacionada con el área curricular"
                        )
                    else:
                        # Si no hay área o no se encontraron competencias, mostrar todas
                        todas_competencias = obtener_todas_las_competencias()
                        if todas_competencias:
                            competencias_opciones = [formatear_competencia_para_tabla(comp) for comp in todas_competencias]
                            competencia_seleccionada = st.selectbox(
                                "🎯 Competencia (opcional - se usará como referencia)",
                                options=[""] + competencias_opciones,
                                help="Selecciona una competencia del Currículo Nacional"
                            )
                except Exception:
                    # Si hay algún error, simplemente no mostrar el selector
                    competencia_seleccionada = ""
            
            grado = st.text_input(
                "🎓 Grado",
                placeholder="Ej: 3, 4, 5",
                help="Grado del nivel educativo (Secundaria)"
            )
            
            generar = st.form_submit_button("🎯 Generar Unidad Didáctica", use_container_width=True)
        
        # FUERA del formulario - manejar resultados
        if generar:
            if not area_curricular.strip():
                st.warning("⚠️ Por favor ingresa un área curricular")
            elif not grado.strip():
                st.warning("⚠️ Por favor ingresa el grado")
            else:
                with st.spinner('🔄 Generando unidad didáctica...'):
                    try:
                        # Pasar la competencia seleccionada si existe y está disponible
                        competencia_para_generar = None
                        if COMPETENCIAS_DISPONIBLES and 'competencia_seleccionada' in locals() and competencia_seleccionada:
                            competencia_para_generar = competencia_seleccionada
                        resultado_raw = generar_unidad_didactica(area_curricular, grado, competencia_para_generar)
                        
                        # Formatear el contenido con encabezados y estructura completa
                        contenido_formateado = formatear_unidad_didactica(resultado_raw, area_curricular)
                        
                        # Guardar archivos automáticamente en Desktop
                        fecha_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                        nombre_txt = f"unidad_didactica_{fecha_str}.txt"
                        ruta_txt = guardar_archivo_desktop(contenido_formateado, nombre_txt, es_bytes=False)
                        
                        if DOCX_OK:
                            doc_bytes = crear_documento_profesional(resultado_raw, "Unidad Didáctica", f"Área: {area_curricular}")
                            if doc_bytes:
                                nombre_docx = f"unidad_didactica_{fecha_str}.docx"
                                ruta_docx = guardar_archivo_desktop(doc_bytes, nombre_docx, es_bytes=True)
                        else:
                            doc_bytes = None
                            ruta_docx = None
                        
                        # Extraer título de la unidad didáctica y títulos de sesiones
                        titulo_unidad = extraer_titulo_unidad_didactica(resultado_raw)
                        if not titulo_unidad:
                            titulo_unidad = f"Unidad Didáctica - {area_curricular}"
                        
                        titulos_sesiones = extraer_titulos_sesiones_unidad(resultado_raw)
                        
                        # Guardar en sesión para usar en sesión de aprendizaje
                        st.session_state['unidad_generada'] = {
                            'titulo': titulo_unidad,
                            'area_curricular': area_curricular,
                            'grado': grado,
                            'contenido': resultado_raw,
                            'titulos_sesiones': titulos_sesiones
                        }
                        
                        # Mensaje de éxito con ubicación
                        st.success("✅ ¡Unidad didáctica generada exitosamente!")
                        if ruta_txt:
                            st.info(f"📁 Archivos guardados en: {ruta_txt.rsplit('/', 1)[0]}")
                        
                        # Mostrar resultado formateado
                        st.markdown("---")
                        st.markdown(contenido_formateado)
                        st.markdown("---")
                        
                        # Botones de descarga
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.download_button(
                                "📄 Descargar TXT",
                                data=contenido_formateado,
                                file_name=f"unidad_didactica_{fecha_str}.txt",
                                mime="text/plain",
                                key="download_txt_unidad",
                                use_container_width=True
                            )
                        
                        with col2:
                            if DOCX_OK and doc_bytes:
                                st.download_button(
                                    "📝 Descargar WORD",
                                    data=doc_bytes,
                                    file_name=f"unidad_didactica_{fecha_str}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key="download_docx_unidad",
                                    use_container_width=True
                                )
                            else:
                                st.button("📝 WORD no disponible", disabled=True, key="docx_disabled_unidad", use_container_width=True)
                        
                        with col3:
                            # Botón para generar nueva unidad
                            if st.button("🔄 Generar Nueva", key="nueva_unidad", use_container_width=True):
                                st.rerun()
                                
                    except Exception as e:
                        st.error(f"❌ Error generando unidad didáctica: {str(e)}")
                        st.info("💡 Verifica la conexión con AWS Bedrock")
    
    with tab2:
        st.header("📖 Generador de Sesión de Aprendizaje")
        
        # Información contextual
        with st.expander("ℹ️ Información sobre la Sesión de Aprendizaje"):
            st.markdown("""
            **¿Qué incluye una sesión de aprendizaje?**
            - ✅ Competencias y capacidades a desarrollar
            - ✅ Secuencia didáctica (inicio, desarrollo, cierre)
            - ✅ Actividades de aprendizaje
            - ✅ Materiales y recursos
            - ✅ Evaluación formativa
            
            **Basado en:** Currículo Nacional de Educación Básica - MINEDU Perú
            """)
        
        # Mostrar información de unidad generada si existe
        if 'unidad_generada' in st.session_state:
            unidad_info = st.session_state['unidad_generada']
            st.info(f"📚 Unidad generada: {unidad_info.get('titulo', 'N/A')}")
            # Mostrar títulos de sesiones disponibles si existen
            titulos_sesiones = unidad_info.get('titulos_sesiones', [])
            if titulos_sesiones:
                st.success(f"📋 Se encontraron {len(titulos_sesiones)} sesiones en la unidad:")
                for idx, titulo_ses in enumerate(titulos_sesiones[:6], 1):  # Mostrar máximo 6
                    st.text(f"  {idx}. {titulo_ses}")
        
        with st.form("form_sesion", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                # Título de la unidad (viene de lo que se generó antes)
                titulo_unidad = st.text_input(
                    "📚 Título de la Unidad",
                    value=st.session_state.get('unidad_generada', {}).get('titulo', ''),
                    placeholder="Ej: La Materia y sus Propiedades",
                    help="Título de la unidad didáctica generada anteriormente"
                )
                
                # Título de la sesión - mostrar selector si hay sesiones disponibles
                titulos_sesiones_disponibles = st.session_state.get('unidad_generada', {}).get('titulos_sesiones', [])
                if titulos_sesiones_disponibles:
                    titulo_sesion_seleccionado = st.selectbox(
                        "🎯 Título de la Sesión (selecciona de la unidad)",
                        options=[""] + titulos_sesiones_disponibles,
                        help="Puedes seleccionar una sesión de la unidad o escribir un título nuevo abajo"
                    )
                    titulo_sesion_personalizado = st.text_input(
                        "O escribe un título personalizado",
                        value="",
                        placeholder="Ej: Identificamos las propiedades de la materia",
                        help="Título específico de la sesión de aprendizaje (se usará este si está lleno, o el seleccionado arriba)"
                    )
                    # Determinar qué título usar: personalizado tiene prioridad
                    titulo_sesion = titulo_sesion_personalizado.strip() if titulo_sesion_personalizado.strip() else (titulo_sesion_seleccionado if titulo_sesion_seleccionado else "")
                else:
                    titulo_sesion = st.text_input(
                        "🎯 Título de la Sesión",
                        placeholder="Ej: Identificamos las propiedades de la materia",
                        help="Título específico de la sesión de aprendizaje"
                    )
                
                # Nivel fijo: Solo Secundaria
                nivel = "Secundaria"
                st.text_input(
                    "📊 Nivel",
                    value=nivel,
                    disabled=True,
                    help="Nivel educativo (limitado a Secundaria)"
                )
            
            with col2:
                # Mostrar grado de la unidad generada (si existe)
                grado_unidad = st.session_state.get('unidad_generada', {}).get('grado', '')
                if grado_unidad:
                    st.text_input(
                        "🎓 Grado",
                        value=grado_unidad,
                        disabled=True,
                        help="Grado obtenido de la unidad didáctica generada"
                    )
                    grado = grado_unidad
                else:
                    st.info("ℹ️ Genera primero una unidad didáctica para obtener el grado")
                    grado = ""
                
                seccion = st.text_input(
                    "👥 Sección",
                    placeholder="Ej: A, B, C",
                    help="Sección del grado"
                )
                
                duracion = st.text_input(
                    "⏱️ Duración",
                    placeholder="Ej: 90 minutos, 2 horas",
                    help="Duración de la sesión de aprendizaje"
                )
            
            generar = st.form_submit_button("🎯 Generar Sesión de Aprendizaje", use_container_width=True)
        
        # FUERA del formulario - manejar resultados
        if generar:
            # Asegurar que todos los campos sean strings
            titulo_unidad = str(titulo_unidad) if titulo_unidad else ''
            titulo_sesion = str(titulo_sesion) if titulo_sesion else ''
            seccion = str(seccion) if seccion else ''
            duracion = str(duracion) if duracion else ''
            
            # Obtener grado de la unidad generada si no está en el formulario
            grado_actual = str(grado) if 'grado' in locals() and grado else ''
            if not grado_actual and 'unidad_generada' in st.session_state:
                grado_actual = str(st.session_state['unidad_generada'].get('grado', '') or '')
            
            # Validar campos requeridos
            if not titulo_unidad.strip():
                st.warning("⚠️ Por favor ingresa el título de la unidad")
            elif not titulo_sesion.strip():
                st.warning("⚠️ Por favor ingresa el título de la sesión")
            elif not nivel:
                st.warning("⚠️ Por favor selecciona el nivel")
            elif not grado_actual.strip():
                st.warning("⚠️ Por favor genera primero una unidad didáctica para obtener el grado")
            elif not seccion.strip():
                st.warning("⚠️ Por favor ingresa la sección")
            elif not duracion.strip():
                st.warning("⚠️ Por favor ingresa la duración")
            else:
                with st.spinner('🔄 Generando sesión de aprendizaje...'):
                    try:
                        resultado_raw = generar_sesion_aprendizaje(
                            titulo_unidad,
                            titulo_sesion,
                            nivel,
                            grado_actual,
                            seccion,
                            duracion
                        )
                        
                        # Formatear el contenido con encabezados y estructura completa
                        contenido_formateado = formatear_sesion_aprendizaje(
                            resultado_raw,
                            titulo_unidad,
                            titulo_sesion,
                            nivel,
                            grado_actual,
                            seccion,
                            duracion
                        )
                        
                        # Guardar archivos automáticamente en Desktop
                        fecha_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                        nombre_txt = f"sesion_aprendizaje_{fecha_str}.txt"
                        ruta_txt = guardar_archivo_desktop(contenido_formateado, nombre_txt, es_bytes=False)
                        
                        if DOCX_OK:
                            # Crear documento con título de unidad y título de sesión
                            doc_bytes = crear_documento_sesion_aprendizaje(
                                resultado_raw,
                                titulo_unidad,
                                titulo_sesion,
                                nivel,
                                grado_actual,
                                seccion
                            )
                            if doc_bytes:
                                nombre_docx = f"sesion_aprendizaje_{fecha_str}.docx"
                                ruta_docx = guardar_archivo_desktop(doc_bytes, nombre_docx, es_bytes=True)
                        else:
                            doc_bytes = None
                            ruta_docx = None
                        
                        # Mensaje de éxito con ubicación
                        st.success("✅ ¡Sesión de aprendizaje generada exitosamente!")
                        if ruta_txt:
                            st.info(f"📁 Archivos guardados en: {ruta_txt.rsplit('/', 1)[0]}")
                        
                        # Mostrar resultado formateado
                        st.markdown("---")
                        st.markdown(contenido_formateado)
                        st.markdown("---")
                        
                        # Botones de descarga
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.download_button(
                                "📄 Descargar TXT",
                                data=contenido_formateado,
                                file_name=f"sesion_aprendizaje_{fecha_str}.txt",
                                mime="text/plain",
                                key="download_txt_sesion",
                                use_container_width=True
                            )
                        
                        with col2:
                            if DOCX_OK and doc_bytes:
                                st.download_button(
                                    "📝 Descargar WORD",
                                    data=doc_bytes,
                                    file_name=f"sesion_aprendizaje_{fecha_str}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key="download_docx_sesion",
                                    use_container_width=True
                                )
                            else:
                                st.button("📝 WORD no disponible", disabled=True, key="docx_disabled_sesion", use_container_width=True)
                        
                        with col3:
                            # Botón para generar nueva sesión
                            if st.button("🔄 Generar Nueva", key="nueva_sesion", use_container_width=True):
                                st.rerun()
                                
                    except Exception as e:
                        st.error(f"❌ Error generando sesión de aprendizaje: {str(e)}")
                        st.info("💡 Verifica la conexión con AWS Bedrock")

else:
    st.error("⚠️ Los servicios no están disponibles. Verifica la configuración.")
    
    with st.expander("🔧 Información de diagnóstico"):
        st.write(f"**Archivo actual:** {__file__}")
        st.write(f"**Directorio actual:** {os.getcwd()}")
        st.write(f"**Directorio del archivo:** {os.path.dirname(__file__)}")
        st.write(f"**Directorio padre:** {os.path.dirname(os.path.dirname(__file__))}")
        
        core_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core')
        st.write(f"**Buscando core en:** {core_path}")
        st.write(f"**Core existe:** {os.path.exists(core_path)}")
        
        if os.path.exists(core_path):
            st.write(f"**Archivos en core:** {os.listdir(core_path)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
<h6>🎓 Sistema de Generación de Contenido Educativo con IA</h6>
<p><em>Desarrollado para el Ministerio de Educación del Perú</em></p>
</div>
""", unsafe_allow_html=True)