"""
Módulo para gestionar las competencias del Currículo Nacional de Educación Básica del Perú.
Contiene las 31 competencias oficiales del MINEDU.
"""

COMPETENCIAS_CURRICULARES = [
    {
        "numero": 1,
        "nombre": "Construye su identidad",
        "descripcion": "Construye su identidad"
    },
    {
        "numero": 2,
        "nombre": "Asume una vida saludable",
        "descripcion": "Asume una vida saludable"
    },
    {
        "numero": 3,
        "nombre": "Se desenvuelve de manera autónoma a través de su motricidad",
        "descripcion": "Se desenvuelve de manera autónoma a través de su motricidad"
    },
    {
        "numero": 4,
        "nombre": "Se comunica oralmente en su lengua materna",
        "descripcion": "Se comunica oralmente en su lengua materna"
    },
    {
        "numero": 5,
        "nombre": "Lee diversos tipos de textos escritos en su lengua materna",
        "descripcion": "Lee diversos tipos de textos escritos en su lengua materna"
    },
    {
        "numero": 6,
        "nombre": "Escribe diversos tipos de textos en su lengua materna",
        "descripcion": "Escribe diversos tipos de textos en su lengua materna"
    },
    {
        "numero": 7,
        "nombre": "Se comunica en inglés como lengua extranjera",
        "descripcion": "Se comunica en inglés como lengua extranjera"
    },
    {
        "numero": 8,
        "nombre": "Resuelve problemas de cantidad",
        "descripcion": "Resuelve problemas de cantidad"
    },
    {
        "numero": 9,
        "nombre": "Resuelve problemas de regularidad, equivalencia y cambio",
        "descripcion": "Resuelve problemas de regularidad, equivalencia y cambio"
    },
    {
        "numero": 10,
        "nombre": "Resuelve problemas de forma, movimiento y localización",
        "descripcion": "Resuelve problemas de forma, movimiento y localización"
    },
    {
        "numero": 11,
        "nombre": "Resuelve problemas de gestión de datos e incertidumbre",
        "descripcion": "Resuelve problemas de gestión de datos e incertidumbre"
    },
    {
        "numero": 12,
        "nombre": "Indaga mediante métodos científicos para construir conocimientos",
        "descripcion": "Indaga mediante métodos científicos para construir conocimientos"
    },
    {
        "numero": 13,
        "nombre": "Explica el mundo físico basándose en conocimientos sobre los seres vivos; materia y energía; biodiversidad, Tierra y universo",
        "descripcion": "Explica el mundo físico basándose en conocimientos sobre los seres vivos; materia y energía; biodiversidad, Tierra y universo"
    },
    {
        "numero": 14,
        "nombre": "Diseña y construye soluciones tecnológicas para resolver problemas de su entorno",
        "descripcion": "Diseña y construye soluciones tecnológicas para resolver problemas de su entorno"
    },
    {
        "numero": 15,
        "nombre": "Gestiona proyectos de emprendimiento económico o social",
        "descripcion": "Gestiona proyectos de emprendimiento económico o social"
    },
    {
        "numero": 16,
        "nombre": "Se desenvuelve en entornos virtuales generados por las TIC",
        "descripcion": "Se desenvuelve en entornos virtuales generados por las TIC"
    },
    {
        "numero": 17,
        "nombre": "Interpreta la realidad y se integra a través de las manifestaciones artístico-culturales",
        "descripcion": "Interpreta la realidad y se integra a través de las manifestaciones artístico-culturales"
    },
    {
        "numero": 18,
        "nombre": "Crea proyectos desde los lenguajes artísticos",
        "descripcion": "Crea proyectos desde los lenguajes artísticos"
    },
    {
        "numero": 19,
        "nombre": "Construye interpretaciones históricas",
        "descripcion": "Construye interpretaciones históricas"
    },
    {
        "numero": 20,
        "nombre": "Gestiona responsablemente el espacio y el ambiente",
        "descripcion": "Gestiona responsablemente el espacio y el ambiente"
    },
    {
        "numero": 21,
        "nombre": "Gestiona responsablemente los recursos económicos",
        "descripcion": "Gestiona responsablemente los recursos económicos"
    },
    {
        "numero": 22,
        "nombre": "Se valora a sí mismo",
        "descripcion": "Se valora a sí mismo"
    },
    {
        "numero": 23,
        "nombre": "Autorregula sus emociones",
        "descripcion": "Autorregula sus emociones"
    },
    {
        "numero": 24,
        "nombre": "Reflexiona y argumenta éticamente",
        "descripcion": "Reflexiona y argumenta éticamente"
    },
    {
        "numero": 25,
        "nombre": "Vive su sexualidad de manera plena y responsable",
        "descripcion": "Vive su sexualidad de manera plena y responsable"
    },
    {
        "numero": 26,
        "nombre": "Interactúa con todas las personas",
        "descripcion": "Interactúa con todas las personas"
    },
    {
        "numero": 27,
        "nombre": "Construye normas y asume acuerdos y leyes",
        "descripcion": "Construye normas y asume acuerdos y leyes"
    },
    {
        "numero": 28,
        "nombre": "Maneja conflictos de manera constructiva",
        "descripcion": "Maneja conflictos de manera constructiva"
    },
    {
        "numero": 29,
        "nombre": "Participa en acciones que promueven el bienestar común",
        "descripcion": "Participa en acciones que promueven el bienestar común"
    },
    {
        "numero": 30,
        "nombre": "Asume la experiencia del encuentro personal y comunitario con Dios en su proyecto de vida en coherencia con su creencia religiosa",
        "descripcion": "Asume la experiencia del encuentro personal y comunitario con Dios en su proyecto de vida en coherencia con su creencia religiosa"
    },
    {
        "numero": 31,
        "nombre": "Conoce a Dios y asume su identidad religiosa como persona digna, libre y trascendente, desarrollando su conciencia moral y orientando su vida desde su encuentro personal y comunitario con Dios",
        "descripcion": "Conoce a Dios y asume su identidad religiosa como persona digna, libre y trascendente, desarrollando su conciencia moral y orientando su vida desde su encuentro personal y comunitario con Dios"
    }
]


def obtener_competencia_por_numero(numero):
    """
    Obtiene una competencia por su número.
    
    Args:
        numero: Número de la competencia (1-31)
        
    Returns:
        Diccionario con la información de la competencia o None si no existe
    """
    try:
        for competencia in COMPETENCIAS_CURRICULARES:
            if competencia["numero"] == numero:
                return competencia
        return None
    except Exception:
        return None


def obtener_competencia_por_nombre(nombre):
    """
    Busca una competencia por su nombre (búsqueda parcial).
    
    Args:
        nombre: Nombre o parte del nombre de la competencia
        
    Returns:
        Lista de competencias que coinciden con el nombre
    """
    try:
        if not nombre:
            return []
        nombre_lower = nombre.lower()
        return [
            competencia for competencia in COMPETENCIAS_CURRICULARES
            if nombre_lower in competencia["nombre"].lower()
        ]
    except Exception:
        return []


def obtener_todas_las_competencias():
    """
    Obtiene todas las competencias curriculares.
    
    Returns:
        Lista con todas las competencias
    """
    try:
        return COMPETENCIAS_CURRICULARES.copy()
    except Exception:
        return []


def obtener_competencias_por_area(area_curricular):
    """
    Obtiene competencias relacionadas con un área curricular específica.
    
    Args:
        area_curricular: Nombre del área curricular (ej: "Ciencia y Tecnología", "Matemática")
        
    Returns:
        Lista de competencias relacionadas con el área
    """
    try:
        if not area_curricular:
            return []
        
        area_lower = area_curricular.lower()
        
        # Mapeo de áreas curriculares a números de competencias
        mapeo_areas = {
            "ciencia y tecnología": [12, 13, 14],
            "ciencia": [12, 13, 14],
            "tecnología": [12, 13, 14],
            "matemática": [8, 9, 10, 11],
            "matematica": [8, 9, 10, 11],
            "comunicación": [4, 5, 6, 7],
            "comunicacion": [4, 5, 6, 7],
            "educación física": [3],
            "educacion fisica": [3],
            "arte y cultura": [17, 18],
            "arte": [17, 18],
            "cultura": [17, 18],
            "historia": [19],
            "geografía": [20],
            "geografia": [20],
            "economía": [21],
            "economia": [21],
            "educación religiosa": [30, 31],
            "educacion religiosa": [30, 31],
            "tutoría": [1, 2, 22, 23, 24, 25, 26, 27, 28, 29],
            "tutoria": [1, 2, 22, 23, 24, 25, 26, 27, 28, 29],
            "educación para el trabajo": [15, 16],
            "educacion para el trabajo": [15, 16]
        }
        
        # Buscar en el mapeo
        competencias_numeros = []
        for area_key, numeros in mapeo_areas.items():
            if area_key in area_lower or area_lower in area_key:
                competencias_numeros = numeros
                break
        
        # Si no se encuentra en el mapeo, buscar por palabras clave
        if not competencias_numeros:
            if "ciencia" in area_lower or "tecnología" in area_lower or "tecnologia" in area_lower:
                competencias_numeros = [12, 13, 14]
            elif "matemática" in area_lower or "matematica" in area_lower:
                competencias_numeros = [8, 9, 10, 11]
            elif "comunicación" in area_lower or "comunicacion" in area_lower:
                competencias_numeros = [4, 5, 6, 7]
        
        return [
            competencia for competencia in COMPETENCIAS_CURRICULARES
            if competencia["numero"] in competencias_numeros
        ]
    except Exception:
        return []


def formatear_competencia_para_tabla(competencia):
    """
    Formatea una competencia para mostrarla en formato de tabla.
    
    Args:
        competencia: Diccionario con la información de la competencia
        
    Returns:
        String formateado: "COMPETENCIA X. Nombre"
    """
    try:
        if not competencia or "numero" not in competencia or "nombre" not in competencia:
            return ""
        return f"COMPETENCIA {competencia['numero']}. {competencia['nombre']}"
    except Exception:
        return ""


def obtener_lista_competencias_formateada():
    """
    Obtiene todas las competencias formateadas para mostrar en una lista.
    
    Returns:
        Lista de strings con formato "COMPETENCIA X. Nombre"
    """
    try:
        return [formatear_competencia_para_tabla(comp) for comp in COMPETENCIAS_CURRICULARES]
    except Exception:
        return []
