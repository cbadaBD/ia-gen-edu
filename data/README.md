# Datos para RAG (Currículo y orientaciones)

## `curriculo_secundaria_peru_2016.json`

Estructura del **Programa Curricular de Educación Secundaria – Perú (2016)** para el RAG del proyecto.

- **Base legal:** RM N°649-2016-MINEDU, vigencia desde 01/01/2017.
- **Contenido:** Perfil de egreso, ciclos VI y VII, enfoques transversales, 11 áreas curriculares, competencias transversales, orientaciones pedagógicas, estándares y desempeños.

### Estructura del JSON

- `metadata`: documento, país, año, nivel_educativo, ciclos, grados, resolución, vigencia_desde, estructura.
- `keywords`: palabras clave para búsqueda (currículo nacional perú 2016, educación secundaria, competencias curriculares, etc.).
- `chunks`: fragmentos con `id`, `section`, `text`, `keywords` para recuperación por sección y contenido.

---

## `orientaciones_pedagogicas_cneb.json`

**Orientaciones para planificación, mediación y evaluación** bajo el CNEB (Currículo Nacional de la Educación Básica), dirigidas a docentes de secundaria.

- **Objetivo:** Planificar, mediar y evaluar aprendizajes con enfoque por competencias y evaluación formativa.
- **Contenido:** Conceptos clave (competencia, evaluación formativa, zona de desarrollo próximo, tarea auténtica, retroalimentación descriptiva), procesos (planificación, mediación, evaluación), pasos para planificar, tipos de planificación (anual, unidad didáctica, sesión), herramientas (rúbricas, evidencias), retroalimentación efectiva, contextualización y diversificación, enfoque en el adolescente, documentos de referencia (CNEB, MBDD, Programa Curricular Secundaria).

### Estructura del JSON

- `metadata`: documento, país, referencia, destinatarios, enfoque.
- `keywords`: planificación curricular, evaluación formativa, competencia, CNEB, mediación, retroalimentación, tarea auténtica, rúbricas, unidad didáctica, sesión de aprendizaje, contextualización, MBDD, etc.
- `chunks`: 10 secciones (objetivo, conceptos clave, procesos, pasos planificar, tipos planificación, herramientas, retroalimentación, contextualización, adolescente, documentos referencia).

---

## Uso en el proyecto

- **RAG local:** El servicio `core/rag_service.py` carga ambos JSON y los usa como fallback cuando Bedrock Knowledge Base no está configurado. La búsqueda combina resultados del currículo y de las orientaciones pedagógicas, ordenados por relevancia.
- **Bedrock Knowledge Base:** Para usar el currículo en una KB de AWS, súbelo a S3 bajo el prefijo `curriculo/`:
  ```bash
  python upload_curriculo.py
  ```
  (Configura `S3_CURRICULO_BUCKET` en `.env` si usas otro bucket; por defecto `minedu-educacion-peru`.)
