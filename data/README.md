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

## `sesion_ef_ept_planificacion_curricular.json`

**Sesión 2 - EF/EPT - Planificación Curricular para plataforma** (origen: PDF “Sesión 2_EF_EPT_Planificación Curricular - EF -EPT - para plataforma”).

- **Propósito:** Formar a docentes en la planificación curricular desde el enfoque por competencias y el carisma salesiano.
- **Áreas:** Educación Física (EF), Educación para el Trabajo (EPT).
- **Contenido:** Objetivo y evidencia de la sesión, agenda, enfoque por competencias (MINEDU 2017), articulación con el carisma salesiano (cuatro saberes de Delors), principios salesianos (Conocer el Patio, Acoger, Unir Vida y Fe), elementos esenciales de la planificación, ejemplos aplicados (4to EPT, 2do EF), secuencia didáctica, rol del docente como diseñador de experiencias, actividad de cierre “Mi planificación transformada”, trabajo en casa (aula invertida), producto final del módulo.

### Estructura del JSON

- `metadata`: documento, origen, propósito_principal, áreas, nivel, enfoque.
- `keywords`: planificación curricular, enfoque por competencias, carisma salesiano, EF, EPT, secuencia didáctica, situaciones significativas, cuatro saberes Delors, principios salesianos, etc.
- `chunks`: 13 secciones (objetivo/evidencia, agenda, enfoque MINEDU, carisma salesiano, principios salesianos, elementos esenciales, ejemplos EPT/EF, secuencia didáctica, rol docente, actividad cierre, trabajo en casa, producto final).

---

## `sesion_3_evaluacion_formativa_ef_ept.json`

**Sesión 3 - La Evaluación Formativa - EF/EPT** (origen: PDF “Sesión 3_La evaluacion formativa - EF_EPT.pdf”). Módulo I – Enfoque por competencias.

- **Propósito:** Comprender la evaluación formativa desde el enfoque por competencias y su sentido salesiano, y diseñar instrumentos alineados a evidencias reales.
- **Áreas:** Educación Física (EF), Educación para el Trabajo (EPT).
- **Contenido:** Propósito y evidencias esperadas de la sesión; qué es la evaluación formativa; enfoque salesiano de la evaluación; elementos de la evaluación formativa; evidencias de aprendizaje (producciones, actuaciones); retroalimentación formativa; actividades prácticas (El Eco de lo que aprendí, diseño de instrumento, Mi instrumento transformado); preguntas guía; autoevaluación Mirar–Agradecer–Proyectar; producto final del módulo 1 (Aula 09).

### Estructura del JSON

- `metadata`: documento, origen, módulo, sesión, propósito_principal, áreas, nivel, enfoque.
- `keywords`: evaluación formativa, enfoque por competencias, sentido salesiano, evidencias de aprendizaje, instrumentos de evaluación, retroalimentación formativa, rúbrica, lista de cotejo, autorregulación, valores salesianos, etc.
- `chunks`: 12 secciones (propósito, evidencias esperadas, qué es evaluación formativa, enfoque salesiano, elementos, evidencias de aprendizaje, retroalimentación formativa, actividades 1–3, preguntas guía, autoevaluación, producto final módulo 1).

---

## `enfoque_por_competencias_modulo1.json`

**Enfoque por competencias - Módulo 1** (origen: PDF “Enfoque por competencias.pdf”). Curso: CAPACITACIÓN – Planificación Curricular por Competencias y Metodologías Activas.

- **Propósito general:** Formar docentes en el enfoque por competencias, su articulación con el carisma salesiano y su aplicación en planificación y evaluación formativa.
- **Contenido:** Competencia y producto final del módulo; Sección 1 – Enfoque basado en competencias (qué es, convergencia salesiana, componentes saber/saber hacer/saber ser, capacidades Nussbaum, fundamentos Piaget/Vygotsky/Lave/Don Bosco, características); Sección 2 – Planificación curricular (sentido, PEPS, principios conocer el patio/acoger/unir escuela vida fe, elementos esenciales, secuencia didáctica); Sección 3 – Evaluación formativa (definición, elementos clave, evidencias, retroalimentación Nicol, tabla de instrumentos); actividades prácticas por sesión; producto final (portafolio docente).

### Estructura del JSON

- `metadata`: documento, origen, curso, módulo, propósito_general, nivel, enfoque.
- `keywords`: enfoque por competencias, carisma salesiano, PEPS, sistema preventivo, Don Bosco, Nussbaum, Perrenoud, situaciones significativas, secuencia didáctica, evaluación formativa, rúbrica, lista de cotejo, portafolio, etc.
- `chunks`: 19 secciones (competencia/producto, sesiones 1–3 propósito y desarrollo, componentes, capacidades, fundamentos, características, PEPS, principios, elementos, secuencia, evaluación formativa, evidencias, retroalimentación, instrumentos, actividades prácticas, producto final).

---

## Uso en el proyecto

- **RAG local:** El servicio `core/rag_service.py` carga los cinco JSON (currículo, orientaciones, sesión 2 EF/EPT, sesión 3 evaluación formativa, enfoque por competencias módulo 1) y los usa como fallback cuando Bedrock Knowledge Base no está configurado. La búsqueda combina resultados de las cinco fuentes, ordenados por relevancia (top 8 currículo, top 6 orientaciones, top 5 por cada uno de los otros tres; luego se reordenan y se devuelven hasta 10 documentos).
- **Bedrock Knowledge Base:** Para usar el currículo en una KB de AWS, súbelo a S3 bajo el prefijo `curriculo/`:
  ```bash
  python upload_curriculo.py
  ```
  (Configura `S3_CURRICULO_BUCKET` en `.env` si usas otro bucket; por defecto `minedu-educacion-peru`.)
