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
            extraer_titulos_sesiones_unidad,
            mejorar_documento_con_instruccion,
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
            formatear_competencia_para_tabla,
            obtener_areas_curriculares_secundaria,
            obtener_grados_secundaria,
        )
        COMPETENCIAS_DISPONIBLES = True
    except Exception:
        # Si falla la importación, simplemente no mostrar el selector de competencias
        COMPETENCIAS_DISPONIBLES = False

# Fallback para menús de malla curricular si no se puede importar competencias_curriculares
AREAS_MALLA_FALLBACK = [
    "Desarrollo Personal, Ciudadanía y Cívica", "Ciencias Sociales", "Educación Física",
    "Arte y Cultura", "Comunicación", "Castellano como Segunda Lengua",
    "Inglés como Lengua Extranjera", "Matemática", "Ciencia y Tecnología",
    "Educación para el Trabajo", "Educación Religiosa",
]
GRADOS_MALLA_FALLBACK = ["1°", "2°", "3°", "4°", "5°"]

def dividir_contenido_largo_en_filas(item, contenido):
    """
    Divide el contenido largo de una celda en múltiples filas.
    Si el contenido tiene saltos de línea, cada línea adicional se convierte en una nueva fila
    con una celda vacía en la columna ITEM para mantener la alineación.
    
    Args:
        item: Texto del item (columna izquierda)
        contenido: Texto del contenido (columna derecha), puede tener saltos de línea
        
    Returns:
        Lista de filas de tabla en formato [item, contenido]
    """
    if not contenido:
        return [[item, ""]]
    
    # Dividir el contenido por saltos de línea
    lineas_contenido = contenido.split('\n')
    filas = []
    
    # Primera fila: item + primera línea de contenido
    if lineas_contenido:
        filas.append([item, lineas_contenido[0].strip()])
        
        # Filas adicionales: celda vacía + líneas restantes de contenido
        for linea_restante in lineas_contenido[1:]:
            if linea_restante.strip():  # Solo agregar si la línea no está vacía
                filas.append(["", linea_restante.strip()])  # Celda vacía en ITEM
    
    return filas if filas else [[item, ""]]


def normalizar_tabla_para_streamlit(contenido):
    """
    Normaliza el contenido de tabla para asegurar que siempre tenga formato ITEM | CONTENIDO
    y se muestre correctamente en Streamlit.
    Si encuentra contenido en la columna izquierda que no es un ITEM válido, lo mueve a la derecha.
    Si el contenido tiene saltos de línea, divide en múltiples filas con espacio en blanco en ITEM.
    
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
        if not texto or len(texto.strip()) == 0:
            return False
        # Si está vacío, no es un item válido
        if not texto or texto.strip() == "":
            return False
        # Si es muy largo, probablemente es contenido, no un item
        if len(texto) > 100:
            return False
        
        texto_upper = texto.upper().strip()
        texto_original = texto.strip()
        
        # Excluir frases que son claramente contenido, no items
        frases_contenido = [
            'MATERIALES PARA ESTUDIANTES',
            'MATERIALES PARA DOCENTE',
            'MATERIAL PARA ESTUDIANTES',
            'MATERIAL PARA DOCENTE',
            'PARA ESTUDIANTES',
            'PARA DOCENTE',
            'VALORES:',
            'ENFOQUES:',
            'COMPETENCIA:',
            'CAPACIDADES:',
            'DESEMPEÑOS:',
            'CRITERIOS:',
            'EVIDENCIAS:',
            'INSTRUMENTOS:',
            'RECURSOS:',
            'ACTIVIDADES:',
            'DIFICULTADES:',
            'MEJORAS:',
            'AJUSTES:'
        ]
        
        # Si contiene dos puntos y es una frase descriptiva, es contenido
        if ':' in texto_original and len(texto_original.split(':')) > 1:
            # Verificar si la parte antes de los dos puntos es una frase descriptiva
            parte_antes = texto_original.split(':')[0].strip().upper()
            if any(frase in parte_antes for frase in frases_contenido):
                return False
            # Si tiene más de 3 palabras antes de los dos puntos, probablemente es contenido
            if len(parte_antes.split()) > 3:
                return False
        
        # Si contiene "para" seguido de otra palabra, probablemente es contenido descriptivo
        if ' PARA ' in texto_upper or texto_upper.startswith('PARA '):
            return False
        
        palabras_item = ['TÍTULO', 'SITUACIÓN', 'COMPETENCIA', 'CAPACIDAD', 
                        'EVIDENCIA', 'INSTRUMENTO', 'VALOR', 'SECUENCIA', 
                        'ENFOQUE', 'SESIÓN', 'MATERIAL', 'REFLEXIÓN', 'ESTÁNDAR',
                        'DESEMPEÑO', 'PROPÓSITO', 'ORGANIZACIÓN', 'EVALUACIÓN',
                        'DATOS', 'CRITERIO', 'MOMENTO', 'DIDÁCTICA', 'INFORMATIVOS',
                        'SIGNIFICATIVA', 'PRECISADOS', 'APRENDIZAJE']
        
        # Limpiar formato markdown bold para análisis
        texto_sin_bold = texto_original.replace('**', '').strip()
        texto_sin_bold_upper = texto_sin_bold.upper()
        
        # Solo considerar como item si:
        # 1. Es muy corto y está en mayúsculas (típico de encabezados)
        # 2. Empieza con ** (formato markdown bold) - estos son siempre items
        # 3. Es una palabra clave específica Y no es una frase descriptiva
        es_palabra_clave = any(palabra in texto_sin_bold_upper for palabra in palabras_item)
        
        # Si empieza con **, es definitivamente un item (formato markdown bold)
        if texto_original.strip().startswith('**') and texto_original.strip().endswith('**'):
            # Verificar que no sea una frase de contenido excluida
            texto_limpio = texto_sin_bold_upper
            if not any(frase in texto_limpio for frase in ['MATERIALES PARA', 'PARA ESTUDIANTES', 'PARA DOCENTE']):
                return True
        
        # Si es una palabra clave pero es una frase descriptiva, no es un item
        if es_palabra_clave:
            # Verificar si es solo la palabra clave o una frase
            palabras_texto = texto_sin_bold_upper.split()
            # Si tiene más de 2 palabras y contiene "PARA", es contenido
            if len(palabras_texto) > 2 and 'PARA' in palabras_texto:
                return False
            # Si tiene más de 5 palabras en total y NO está en negrita, probablemente es contenido
            if len(palabras_texto) > 5 and not texto_original.strip().startswith('**'):
                return False
        
        return (
            (len(texto_sin_bold) < 50 and texto_sin_bold.isupper() and len(texto_sin_bold.split()) <= 5) or
            (texto_original.strip().startswith('**') and len(texto_sin_bold.split()) <= 6) or
            (es_palabra_clave and len(texto_sin_bold.split()) <= 5 and not any(frase in texto_sin_bold_upper for frase in ['MATERIALES PARA', 'PARA ESTUDIANTES', 'PARA DOCENTE']))
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
                    if item_ultimo and item_ultimo != "" and (not contenido_ultimo or len(contenido_ultimo) < 30):
                        # La última fila tiene ITEM sin CONTENIDO, agregar este contenido ahí
                        if contenido_ultimo:
                            contenido_combinado = contenido_ultimo + '\n' + contenido_unico
                        else:
                            contenido_combinado = contenido_unico
                        # Dividir contenido largo en múltiples filas
                        filas = dividir_contenido_largo_en_filas(item_ultimo, contenido_combinado)
                        # Reemplazar la última fila con la primera fila dividida
                        if filas:
                            lineas_normalizadas[-1] = f"| {filas[0][0]} | {filas[0][1]} |"
                            # Agregar filas adicionales con espacio en blanco en ITEM
                            for fila_item, fila_contenido in filas[1:]:
                                lineas_normalizadas.append(f"| {fila_item} | {fila_contenido} |")
                    elif es_item:
                        # Es un ITEM nuevo
                        lineas_normalizadas.append(f"| {contenido_unico} | |")
                    else:
                        # Es CONTENIDO pero no hay ITEM previo sin CONTENIDO
                        # Dividir contenido largo en múltiples filas con celda vacía en ITEM
                        filas = dividir_contenido_largo_en_filas("", contenido_unico)
                        for fila_item, fila_contenido in filas:
                            lineas_normalizadas.append(f"| {fila_item} | {fila_contenido} |")
                elif len(fila) >= 2:
                    # Dos o más columnas: verificar si la primera es realmente un ITEM
                    primera_col = fila[0]
                    resto_contenido = ' '.join([c for c in fila[1:] if c])
                    
                    # Limpiar formato markdown bold del item si está presente
                    item_limpio = primera_col.strip()
                    if item_limpio.startswith('**') and item_limpio.endswith('**'):
                        item_limpio = item_limpio[2:-2].strip()
                    
                    # Verificar si es un item válido (usar el texto limpio para verificación)
                    es_item = es_item_valido(primera_col)
                    
                    # Si la primera columna NO es un ITEM válido, mover todo a la derecha
                    if not es_item:
                        # La primera columna es contenido, mover todo a la derecha con celda vacía
                        contenido_completo = primera_col
                        if resto_contenido:
                            contenido_completo = primera_col + ' ' + resto_contenido
                        # Dividir contenido largo en múltiples filas
                        filas = dividir_contenido_largo_en_filas("", contenido_completo)
                        for fila_item, fila_contenido in filas:
                            lineas_normalizadas.append(f"| {fila_item} | {fila_contenido} |")
                    else:
                        # La primera columna es un ITEM válido
                        # Usar el item original (con ** si estaba) para mantener formato
                        # Dividir contenido largo en múltiples filas si tiene saltos de línea
                        filas = dividir_contenido_largo_en_filas(primera_col, resto_contenido)
                        for fila_item, fila_contenido in filas:
                            lineas_normalizadas.append(f"| {fila_item} | {fila_contenido} |")
        else:
            # Línea fuera de tabla (sin formato |)
            if dentro_tabla and linea_stripped:
                # Si estamos dentro de una tabla y encontramos contenido sin |,
                # SIEMPRE agregarlo como nueva fila con espacio en blanco en ITEM
                if (lineas_normalizadas and 
                    lineas_normalizadas[-1].startswith('|') and
                    not linea_stripped.startswith('#') and
                    not re.match(r'^\s*\|[\s\-\:]+\|\s*$', linea_stripped)):
                    item_ultimo, contenido_ultimo, ultima_linea = obtener_ultima_fila_info()
                    if item_ultimo is not None and item_ultimo != "":
                        # Agregar como nueva fila con celda vacía en ITEM
                        # Dividir en múltiples filas si es necesario
                        filas = dividir_contenido_largo_en_filas("", linea_stripped)
                        for fila_item, fila_contenido in filas:
                            lineas_normalizadas.append(f"| {fila_item} | {fila_contenido} |")
                    else:
                        dentro_tabla = False
                        lineas_normalizadas.append(linea)
                else:
                    dentro_tabla = False
                    lineas_normalizadas.append(linea)
            else:
                lineas_normalizadas.append(linea)
        
        i += 1
    
    # Post-procesamiento: dividir contenido largo en las filas finales y corregir items mal ubicados
    lineas_finales = []
    for linea in lineas_normalizadas:
        if '|' in linea and not re.match(r'^\s*\|[\s\-\:]+\|\s*$', linea.strip()):
            # Es una fila de tabla, verificar si el contenido tiene saltos de línea
            partes = linea.split('|')
            if len(partes) >= 3:
                item = partes[1].strip()
                contenido_celda = partes[2].strip()
                
                # Limpiar formato markdown bold del item para análisis
                item_limpio = item.replace('**', '').strip() if item else ""
                item_upper = item_limpio.upper() if item_limpio else ""
                
                # Detectar frases que son claramente contenido, no items
                frases_contenido_detectadas = [
                    'MATERIALES PARA ESTUDIANTES',
                    'MATERIALES PARA DOCENTE',
                    'MATERIAL PARA ESTUDIANTES',
                    'MATERIAL PARA DOCENTE',
                    'PARA ESTUDIANTES',
                    'PARA DOCENTE',
                    'VALORES:',
                    'ENFOQUES:',
                    'COMPETENCIA:',
                    'CAPACIDADES:',
                    'DESEMPEÑOS:',
                    'CRITERIOS:',
                    'EVIDENCIAS:',
                    'INSTRUMENTOS:',
                    'RECURSOS:',
                    'ACTIVIDADES:'
                ]
                
                es_frase_contenido = any(frase in item_upper for frase in frases_contenido_detectadas)
                
                # Si el item contiene ":" y es una frase descriptiva, es contenido
                if item_limpio and ':' in item_limpio:
                    parte_antes = item_limpio.split(':')[0].strip().upper()
                    if any(frase in parte_antes for frase in frases_contenido_detectadas):
                        es_frase_contenido = True
                    # Si tiene más de 3 palabras antes de los dos puntos, probablemente es contenido
                    if len(parte_antes.split()) > 3:
                        es_frase_contenido = True
                
                # Si el item está en negrita (**), es definitivamente un item válido
                es_item_en_negrita = item and item.strip().startswith('**') and item.strip().endswith('**')
                
                # Si el item no es válido O es una frase de contenido (y NO está en negrita), mover todo a la derecha
                if item and (not es_item_valido(item) or es_frase_contenido) and not es_item_en_negrita:
                    # El item es en realidad contenido, mover todo a la derecha
                    if contenido_celda:
                        contenido_completo = item + ' ' + contenido_celda
                    else:
                        contenido_completo = item
                    filas = dividir_contenido_largo_en_filas("", contenido_completo)
                    for fila_item, fila_contenido in filas:
                        lineas_finales.append(f"| {fila_item} | {fila_contenido} |")
                # Si el item está en negrita, mantenerlo en la izquierda y el contenido en la derecha
                elif es_item_en_negrita:
                    # Asegurar que el contenido esté en la columna derecha
                    # Si el contenido está vacío o es muy corto, puede que esté mezclado con el item
                    if not contenido_celda or len(contenido_celda) < 10:
                        # El contenido puede estar en la misma celda que el item, verificar
                        item_limpio = item.replace('**', '').strip()
                        # Si el item tiene contenido después de los **, separarlo
                        if '**' in item and len(item.split('**')) > 2:
                            partes_item = item.split('**')
                            if len(partes_item) >= 3:
                                item_final = '**' + partes_item[1] + '**'
                                contenido_restante = ' '.join(partes_item[2:]).strip()
                                if contenido_restante:
                                    contenido_celda = contenido_restante + (' ' + contenido_celda if contenido_celda else '')
                                    item = item_final
                    
                    # Dividir contenido largo en múltiples filas si es necesario
                    if '\n' in contenido_celda or len(contenido_celda) > 200:
                        filas = dividir_contenido_largo_en_filas(item, contenido_celda)
                        for fila_item, fila_contenido in filas:
                            lineas_finales.append(f"| {fila_item} | {fila_contenido} |")
                    else:
                        lineas_finales.append(f"| {item} | {contenido_celda} |")
                # Si el contenido tiene saltos de línea, dividir en múltiples filas
                elif '\n' in contenido_celda or (len(contenido_celda) > 200 and item):
                    filas = dividir_contenido_largo_en_filas(item, contenido_celda)
                    for fila_item, fila_contenido in filas:
                        lineas_finales.append(f"| {fila_item} | {fila_contenido} |")
                else:
                    lineas_finales.append(linea)
            else:
                lineas_finales.append(linea)
        else:
            lineas_finales.append(linea)
    
    resultado = '\n'.join(lineas_finales)
    
    # Asegurar que las tablas tengan el formato correcto para Streamlit
    # Streamlit requiere una línea separadora después del encabezado
    lineas_resultado = resultado.split('\n')
    lineas_formateadas = []
    dentro_tabla = False
    ultima_fila_era_encabezado = False
    
    i = 0
    while i < len(lineas_resultado):
        linea = lineas_resultado[i]
        linea_stripped = linea.strip()
        
        # Detectar si es una línea de tabla
        if '|' in linea_stripped and linea_stripped.count('|') >= 2:
            # Verificar si es un separador
            es_separador = re.match(r'^\s*\|[\s\-\:]+\|\s*$', linea_stripped)
            
            if es_separador:
                # Ya hay un separador, mantenerlo pero asegurar formato correcto
                num_cols = linea_stripped.count('|') - 1
                separador = '|' + '|'.join(['---' for _ in range(num_cols)]) + '|'
                lineas_formateadas.append(separador)
                dentro_tabla = True
                ultima_fila_era_encabezado = False
            else:
                # Es una fila de datos o encabezado
                # Verificar si es encabezado (contiene ITEM y CONTENIDO)
                es_encabezado = ('ITEM' in linea_stripped.upper() and 'CONTENIDO' in linea_stripped.upper())
                
                # Si la última fila era encabezado y no había separador, agregarlo ahora
                if ultima_fila_era_encabezado:
                    num_cols = lineas_formateadas[-1].count('|') - 1
                    separador = '|' + '|'.join(['---' for _ in range(num_cols)]) + '|'
                    lineas_formateadas.append(separador)
                    ultima_fila_era_encabezado = False
                
                lineas_formateadas.append(linea_stripped)
                dentro_tabla = True
                
                # Si es encabezado, marcar para agregar separador después
                if es_encabezado:
                    # Verificar si la siguiente línea es un separador
                    if i + 1 < len(lineas_resultado):
                        siguiente = lineas_resultado[i + 1].strip()
                        es_sig_separador = re.match(r'^\s*\|[\s\-\:]+\|\s*$', siguiente)
                        if not es_sig_separador:
                            ultima_fila_era_encabezado = True
                    else:
                        # Es la última línea y es encabezado, agregar separador
                        num_cols = linea_stripped.count('|') - 1
                        separador = '|' + '|'.join(['---' for _ in range(num_cols)]) + '|'
                        lineas_formateadas.append(separador)
        else:
            # Si salimos de una tabla y la última fila era encabezado, agregar separador
            if dentro_tabla and ultima_fila_era_encabezado:
                num_cols = lineas_formateadas[-1].count('|') - 1
                separador = '|' + '|'.join(['---' for _ in range(num_cols)]) + '|'
                lineas_formateadas.append(separador)
                ultima_fila_era_encabezado = False
            
            dentro_tabla = False
            if linea_stripped:
                lineas_formateadas.append(linea)
            elif lineas_formateadas and lineas_formateadas[-1].strip():
                lineas_formateadas.append('')
        
        i += 1
    
    # Si terminamos dentro de una tabla y la última fila era encabezado, agregar separador
    if dentro_tabla and ultima_fila_era_encabezado:
        num_cols = lineas_formateadas[-1].count('|') - 1
        separador = '|' + '|'.join(['---' for _ in range(num_cols)]) + '|'
        lineas_formateadas.append(separador)
    
    return '\n'.join(lineas_formateadas)

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
        
        # Inicializar chat desde el inicio
        if 'chat_mensajes_unidad' not in st.session_state:
            st.session_state['chat_mensajes_unidad'] = []
        
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
            # Menús según malla curricular (Programa Curricular Educación Secundaria – Perú 2016)
            # Opción en blanco por defecto; el resto son sugerencias
            lista_areas = obtener_areas_curriculares_secundaria() if COMPETENCIAS_DISPONIBLES else AREAS_MALLA_FALLBACK
            lista_grados = obtener_grados_secundaria() if COMPETENCIAS_DISPONIBLES else GRADOS_MALLA_FALLBACK
            opciones_areas = ["— Seleccione un área curricular —"] + list(lista_areas)
            opciones_grados = ["— Seleccione un grado —"] + list(lista_grados)

            area_curricular = st.selectbox(
                "📚 Área Curricular",
                options=opciones_areas,
                index=0,
                help="Selecciona el área curricular según la malla de Educación Secundaria"
            )
            grado = st.selectbox(
                "🎓 Grado / Curso",
                options=opciones_grados,
                index=0,
                help="Selecciona el grado (curso) de secundaria: 1° a 5°"
            )

            # Selector de competencias con checkboxes (opcional, solo si está disponible)
            # Inicializar session_state para mantener las competencias seleccionadas
            if 'competencias_seleccionadas_unidad' not in st.session_state:
                st.session_state['competencias_seleccionadas_unidad'] = []
            if 'area_curricular_anterior' not in st.session_state:
                st.session_state['area_curricular_anterior'] = ""
            
            # Limpiar competencias si cambió el área curricular
            area_actual = area_curricular.strip() if area_curricular and area_curricular.strip() and not area_curricular.startswith("— Seleccione") else ""
            area_anterior = st.session_state.get('area_curricular_anterior', '')
            
            if area_actual and area_actual != area_anterior:
                # Limpiar competencias cuando cambia el área
                st.session_state['competencias_seleccionadas_unidad'] = []
                st.session_state['area_curricular_anterior'] = area_actual
            elif not area_actual:
                # Si no hay área seleccionada, limpiar también
                st.session_state['competencias_seleccionadas_unidad'] = []
            
            competencias_seleccionadas = []
            if COMPETENCIAS_DISPONIBLES:
                try:
                    competencias_relacionadas = []
                    if area_curricular and area_curricular.strip():
                        competencias_relacionadas = obtener_competencias_por_area(area_curricular.strip())
                    
                    if competencias_relacionadas:
                        competencias_opciones = [formatear_competencia_para_tabla(comp) for comp in competencias_relacionadas]
                        # Filtrar competencias seleccionadas previas que aún están disponibles
                        competencias_previas = st.session_state.get('competencias_seleccionadas_unidad', [])
                        competencias_validas = [c for c in competencias_previas if c in competencias_opciones]
                        # Usar session_state para mantener la selección válida
                        # Asegurar que default sea una lista válida
                        default_competencias = competencias_validas if competencias_validas else []
                        competencias_seleccionadas = st.multiselect(
                            "🎯 Competencias",
                            options=competencias_opciones,
                            help="Selecciona una o más competencias relacionadas con el área curricular",
                            default=default_competencias,
                            key="multiselect_competencias_unidad_area"
                        )
                        # Actualizar session_state con la selección actual siempre
                        st.session_state['competencias_seleccionadas_unidad'] = list(competencias_seleccionadas) if competencias_seleccionadas else []
                    else:
                        # Si no hay área o no se encontraron competencias, mostrar todas
                        todas_competencias = obtener_todas_las_competencias()
                        if todas_competencias:
                            competencias_opciones = [formatear_competencia_para_tabla(comp) for comp in todas_competencias]
                            # Filtrar competencias seleccionadas previas que aún están disponibles
                            competencias_previas = st.session_state.get('competencias_seleccionadas_unidad', [])
                            competencias_validas = [c for c in competencias_previas if c in competencias_opciones]
                            # Asegurar que default sea una lista válida
                            default_competencias = competencias_validas if competencias_validas else []
                            competencias_seleccionadas = st.multiselect(
                                "🎯 Competencias",
                                options=competencias_opciones,
                                help="Selecciona una o más competencias del Currículo Nacional",
                                default=default_competencias,
                                key="multiselect_competencias_unidad_todas"
                            )
                            # Actualizar session_state con la selección actual
                            st.session_state['competencias_seleccionadas_unidad'] = competencias_seleccionadas if competencias_seleccionadas else []
                except Exception:
                    # Si hay algún error, simplemente no mostrar el selector
                    competencias_seleccionadas = []
                    st.session_state['competencias_seleccionadas_unidad'] = []
            
            # Campo para temas
            temas_unidad = st.text_area(
                "📝 Temas (opcional)",
                help="Especifica los temas o contenidos que deseas incluir en la unidad didáctica",
                placeholder="Ejemplo: Temas relacionados con el área curricular seleccionada...",
                height=80
            )
            
            # Campo para número de sesiones
            num_sesiones = st.number_input(
                "🔢 Número de sesiones",
                min_value=4,
                value=6,
                step=1,
                help="Especifica cuántas sesiones de aprendizaje tendrá la unidad didáctica (mínimo 4)"
            )
            
            generar = st.form_submit_button("🎯 Generar Unidad Didáctica", use_container_width=True)
        
        # FUERA del formulario - manejar resultados
        if generar:
            # Tratar la opción por defecto (placeholder) como no seleccionado
            area_vacia = not area_curricular.strip() or area_curricular.startswith("— Seleccione")
            grado_vacio = not grado.strip() or grado.startswith("— Seleccione")
            if area_vacia:
                st.warning("⚠️ Por favor selecciona un área curricular")
            elif grado_vacio:
                st.warning("⚠️ Por favor selecciona un grado")
            else:
                with st.spinner('🔄 Generando unidad didáctica...'):
                    try:
                        # Pasar las competencias seleccionadas si existen y están disponibles
                        competencia_para_generar = None
                        competencias_para_usar = st.session_state.get('competencias_seleccionadas_unidad', [])
                        if COMPETENCIAS_DISPONIBLES and competencias_para_usar:
                            # Si hay múltiples competencias, concatenarlas con saltos de línea
                            if len(competencias_para_usar) > 0:
                                competencia_para_generar = "\n".join(competencias_para_usar)
                        
                        # Obtener temas y número de sesiones del formulario
                        temas_para_generar = temas_unidad.strip() if temas_unidad and temas_unidad.strip() else None
                        num_sesiones_para_generar = num_sesiones if num_sesiones >= 4 else 4
                        
                        resultado_raw = generar_unidad_didactica(
                            area_curricular, 
                            grado, 
                            competencia_referencia=competencia_para_generar,
                            temas=temas_para_generar,
                            num_sesiones=num_sesiones_para_generar
                        )
                        
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
                        # Guardar documento editable y reiniciar chat de mejoras
                        st.session_state['documento_editable_unidad'] = contenido_formateado
                        st.session_state['documento_raw_unidad'] = resultado_raw
                        st.session_state['chat_mensajes_unidad'] = []
                        
                        st.success("✅ ¡Unidad didáctica generada exitosamente!")
                        if ruta_txt:
                            st.info(f"📁 Archivos guardados en: {ruta_txt.rsplit('/', 1)[0]}")
                                
                    except Exception as e:
                        st.error(f"❌ Error generando unidad didáctica: {str(e)}")
                        st.info("💡 Verifica la conexión con AWS Bedrock")
        
        # Mostrar documento actual (generado o mejorado por chat) y chat de mejoras
        if st.session_state.get('documento_editable_unidad'):
            st.markdown("---")
            
            # Sección de documento con expander para mejor organización
            with st.expander("📄 Ver documento actual", expanded=True):
                doc_actual = st.session_state['documento_editable_unidad']
                st.markdown(doc_actual)
            
            # Botones de acción en una fila organizada
            st.markdown("### 📥 Descargar documento")
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                st.download_button(
                    "📄 Descargar TXT",
                    data=doc_actual,
                    file_name=f"unidad_didactica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_txt_unidad",
                    use_container_width=True
                )
            with col2:
                if DOCX_OK:
                    doc_bytes_actual = crear_documento_profesional(
                        st.session_state.get('documento_raw_unidad', doc_actual),
                        "Unidad Didáctica",
                        f"Área: {st.session_state.get('unidad_generada', {}).get('area_curricular', '')}"
                    )
                    if doc_bytes_actual:
                        st.download_button(
                            "📝 Descargar WORD",
                            data=doc_bytes_actual,
                            file_name=f"unidad_didactica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="download_docx_unidad",
                            use_container_width=True
                        )
                    else:
                        st.button("📝 WORD no disponible", disabled=True, key="docx_disabled_unidad", use_container_width=True)
                else:
                    st.button("📝 WORD no disponible", disabled=True, key="docx_disabled_unidad", use_container_width=True)
            with col3:
                if st.button("🔄 Generar Nueva Unidad", key="nueva_unidad", use_container_width=True):
                    for k in ('documento_editable_unidad', 'documento_raw_unidad', 'chat_mensajes_unidad'):
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()
            
            st.markdown("---")
        
        # Chat siempre visible desde el inicio - Mejor organizado
        st.markdown("### 💬 Editor de Chat - Mejorar documento")
        
        # Mostrar estado del documento
        if st.session_state.get('documento_editable_unidad'):
            st.success("✅ Tienes un documento generado. Puedes mejorarlo usando el chat.")
        else:
            st.info("ℹ️ **Genera primero una unidad didáctica arriba para poder mejorarla con el chat.**")
        
        st.info("💡 **Sugerencias:** Puedes pedir cambios como 'haz más breve la sección de criterios', 'mejora el lenguaje', 'añade más ejemplos', etc.")
        
        # Contenedor para el chat con mejor estilo
        chat_container = st.container()
        with chat_container:
            # Mostrar historial de chat con mejor formato
            if st.session_state['chat_mensajes_unidad']:
                st.markdown("#### 📜 Historial de conversación")
                for idx, msg in enumerate(st.session_state['chat_mensajes_unidad']):
                    with st.chat_message(msg["role"]):
                        if msg["role"] == "user":
                            st.markdown(f"**Tu solicitud:**\n{msg['content']}")
                        else:
                            # Mejorar formato de respuesta del asistente
                            contenido = msg['content']
                            if "✅ Cambios aplicados" in contenido:
                                st.success("✅ **Cambios aplicados exitosamente**")
                                # Extraer solo la vista previa si existe
                                if "Vista previa:" in contenido:
                                    partes = contenido.split("Vista previa:", 1)
                                    if len(partes) > 1:
                                        st.markdown(f"**Vista previa:**\n{partes[1].strip()}")
                            elif "❌ Error" in contenido:
                                st.error(contenido)
                            else:
                                st.markdown(contenido)
                    if idx < len(st.session_state['chat_mensajes_unidad']) - 1:
                        st.markdown("---")
            else:
                st.markdown("*No hay mensajes aún. Escribe abajo para comenzar a mejorar el documento.*")
            
            # Input de chat con mejor placeholder (habilitado solo si hay documento)
            tiene_documento = st.session_state.get('documento_editable_unidad')
            prompt_chat = st.chat_input(
                "Escribe aquí cómo quieres mejorar el documento..." if tiene_documento else "Primero genera una unidad didáctica arriba...",
                key="chat_input_unidad",
                disabled=not tiene_documento
            )
            
            if prompt_chat and tiene_documento:
                # Agregar mensaje del usuario al historial
                st.session_state['chat_mensajes_unidad'].append({"role": "user", "content": prompt_chat})
                
                # Mostrar spinner mientras se procesa
                with st.spinner("🔄 Aplicando cambios al documento..."):
                    try:
                        nuevo_doc = mejorar_documento_con_instruccion(
                            st.session_state['documento_editable_unidad'],
                            prompt_chat,
                            "unidad didáctica"
                        )
                        
                        if nuevo_doc and not nuevo_doc.startswith("[Error"):
                            st.session_state['documento_editable_unidad'] = nuevo_doc
                            st.session_state['documento_raw_unidad'] = nuevo_doc
                            # Mensaje de éxito más claro
                            st.session_state['chat_mensajes_unidad'].append({
                                "role": "assistant",
                                "content": f"✅ Cambios aplicados exitosamente. El documento ha sido actualizado.\n\n**Vista previa de los cambios:**\n\n{nuevo_doc[:400]}..."
                            })
                        else:
                            st.session_state['chat_mensajes_unidad'].append({
                                "role": "assistant",
                                "content": f"⚠️ No se pudieron aplicar los cambios. Por favor, intenta con una instrucción más específica."
                            })
                    except Exception as e:
                        st.session_state['chat_mensajes_unidad'].append({
                            "role": "assistant",
                            "content": f"❌ Error al procesar la solicitud: {str(e)}\n\nPor favor, intenta nuevamente."
                        })
                st.rerun()
    
    with tab2:
        st.header("📖 Generador de Sesión de Aprendizaje")
        
        # Inicializar chat desde el inicio
        if 'chat_mensajes_sesion' not in st.session_state:
            st.session_state['chat_mensajes_sesion'] = []
        
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
                        
                        # Guardar documento editable y metadatos para chat y descarga
                        st.session_state['documento_editable_sesion'] = contenido_formateado
                        st.session_state['documento_raw_sesion'] = resultado_raw
                        st.session_state['chat_mensajes_sesion'] = []
                        st.session_state['sesion_meta'] = {
                            'titulo_unidad': titulo_unidad,
                            'titulo_sesion': titulo_sesion,
                            'nivel': nivel,
                            'grado': grado_actual,
                            'seccion': seccion
                        }
                        
                        st.success("✅ ¡Sesión de aprendizaje generada exitosamente!")
                        if ruta_txt:
                            st.info(f"📁 Archivos guardados en: {ruta_txt.rsplit('/', 1)[0]}")
                                
                    except Exception as e:
                        st.error(f"❌ Error generando sesión de aprendizaje: {str(e)}")
                        st.info("💡 Verifica la conexión con AWS Bedrock")
        
        # Mostrar documento actual (generado o mejorado) y chat de mejoras - Sesión
        if st.session_state.get('documento_editable_sesion'):
            st.markdown("---")
            
            # Sección de documento con expander para mejor organización
            with st.expander("📄 Ver documento actual", expanded=True):
                doc_actual_sesion = st.session_state['documento_editable_sesion']
                st.markdown(doc_actual_sesion)
            
            # Botones de acción en una fila organizada
            st.markdown("### 📥 Descargar documento")
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                st.download_button(
                    "📄 Descargar TXT",
                    data=doc_actual_sesion,
                    file_name=f"sesion_aprendizaje_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_txt_sesion",
                    use_container_width=True
                )
            with col2:
                if DOCX_OK:
                    meta = st.session_state.get('sesion_meta', {})
                    doc_bytes_sesion = crear_documento_sesion_aprendizaje(
                        st.session_state.get('documento_raw_sesion', doc_actual_sesion),
                        meta.get('titulo_unidad', ''),
                        meta.get('titulo_sesion', ''),
                        meta.get('nivel', 'Secundaria'),
                        meta.get('grado', ''),
                        meta.get('seccion', '')
                    )
                    if doc_bytes_sesion:
                        st.download_button(
                            "📝 Descargar WORD",
                            data=doc_bytes_sesion,
                            file_name=f"sesion_aprendizaje_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="download_docx_sesion",
                            use_container_width=True
                        )
                    else:
                        st.button("📝 WORD no disponible", disabled=True, key="docx_disabled_sesion", use_container_width=True)
                else:
                    st.button("📝 WORD no disponible", disabled=True, key="docx_disabled_sesion", use_container_width=True)
            with col3:
                if st.button("🔄 Generar Nueva Sesión", key="nueva_sesion", use_container_width=True):
                    for k in ('documento_editable_sesion', 'documento_raw_sesion', 'chat_mensajes_sesion', 'sesion_meta'):
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()
            
            st.markdown("---")
        
        # Chat siempre visible desde el inicio - Mejor organizado
        st.markdown("### 💬 Editor de Chat - Mejorar sesión")
        
        # Mostrar estado del documento
        if st.session_state.get('documento_editable_sesion'):
            st.success("✅ Tienes una sesión generada. Puedes mejorarla usando el chat.")
        else:
            st.info("ℹ️ **Genera primero una sesión de aprendizaje arriba para poder mejorarla con el chat.**")
        
        st.info("💡 **Sugerencias:** Puedes pedir cambios como 'añade una actividad de cierre', 'simplifica las indicaciones', 'mejora la secuencia didáctica', etc.")
        
        # Contenedor para el chat con mejor estilo
        chat_container_sesion = st.container()
        with chat_container_sesion:
            # Mostrar historial de chat con mejor formato
            if st.session_state['chat_mensajes_sesion']:
                st.markdown("#### 📜 Historial de conversación")
                for idx, msg in enumerate(st.session_state['chat_mensajes_sesion']):
                    with st.chat_message(msg["role"]):
                        if msg["role"] == "user":
                            st.markdown(f"**Tu solicitud:**\n{msg['content']}")
                        else:
                            # Mejorar formato de respuesta del asistente
                            contenido = msg['content']
                            if "✅ Cambios aplicados" in contenido:
                                st.success("✅ **Cambios aplicados exitosamente**")
                                # Extraer solo la vista previa si existe
                                if "Vista previa:" in contenido:
                                    partes = contenido.split("Vista previa:", 1)
                                    if len(partes) > 1:
                                        st.markdown(f"**Vista previa:**\n{partes[1].strip()}")
                            elif "❌ Error" in contenido:
                                st.error(contenido)
                            else:
                                st.markdown(contenido)
                    if idx < len(st.session_state['chat_mensajes_sesion']) - 1:
                        st.markdown("---")
            else:
                st.markdown("*No hay mensajes aún. Escribe abajo para comenzar a mejorar la sesión.*")
            
            # Input de chat con mejor placeholder (habilitado solo si hay documento)
            tiene_documento_sesion = st.session_state.get('documento_editable_sesion')
            prompt_sesion = st.chat_input(
                "Escribe aquí cómo quieres mejorar la sesión..." if tiene_documento_sesion else "Primero genera una sesión de aprendizaje arriba...",
                key="chat_input_sesion",
                disabled=not tiene_documento_sesion
            )
            
            if prompt_sesion and tiene_documento_sesion:
                # Agregar mensaje del usuario al historial
                st.session_state['chat_mensajes_sesion'].append({"role": "user", "content": prompt_sesion})
                
                # Mostrar spinner mientras se procesa
                with st.spinner("🔄 Aplicando cambios a la sesión..."):
                    try:
                        nuevo_doc_sesion = mejorar_documento_con_instruccion(
                            st.session_state['documento_editable_sesion'],
                            prompt_sesion,
                            "sesión de aprendizaje"
                        )
                        
                        if nuevo_doc_sesion and not nuevo_doc_sesion.startswith("[Error"):
                            st.session_state['documento_editable_sesion'] = nuevo_doc_sesion
                            st.session_state['documento_raw_sesion'] = nuevo_doc_sesion
                            # Mensaje de éxito más claro
                            st.session_state['chat_mensajes_sesion'].append({
                                "role": "assistant",
                                "content": f"✅ Cambios aplicados exitosamente. La sesión ha sido actualizada.\n\n**Vista previa de los cambios:**\n\n{nuevo_doc_sesion[:400]}..."
                            })
                        else:
                            st.session_state['chat_mensajes_sesion'].append({
                                "role": "assistant",
                                "content": f"⚠️ No se pudieron aplicar los cambios. Por favor, intenta con una instrucción más específica."
                            })
                    except Exception as e:
                        st.session_state['chat_mensajes_sesion'].append({
                            "role": "assistant",
                            "content": f"❌ Error al procesar la solicitud: {str(e)}\n\nPor favor, intenta nuevamente."
                        })
                st.rerun()

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