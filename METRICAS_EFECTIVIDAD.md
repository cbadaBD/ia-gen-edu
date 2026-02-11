## Métricas para evaluar la efectividad del proyecto

Este documento propone métricas (cuantitativas y cualitativas) para evaluar la efectividad del **Generador Educativo AI** a nivel pedagógico, de uso, de calidad de IA y de operación técnica.

---


## 2. Calidad pedagógica de las unidades y sesiones

- **2.1. Alineamiento con el Currículo Nacional (CNEB)**
  - **Definición**: Porcentaje de documentos generados que cumplen criterios de alineamiento (competencias, capacidades, desempeños, enfoques transversales).
  - **Medición**:
    - Rúbrica de revisión experta (0–3 o 0–4) en criterios como:
      - Correspondencia con competencia oficial
      - Coherencia competencia–capacidades–desempeños
      - Inclusión de enfoques transversales pertinentes
    - \( \text{Índice de alineamiento} = \frac{\sum \text{puntuaciones rúbrica}}{\text{puntuación máxima posible}} \)

- **2.2. Claridad y precisión de desempeños**
  - **Definición**: Medida de cuán observables, medibles y pertinentes son los desempeños generados.
  - **Medición**:
    - Revisión experta con rúbrica (claridad, observabilidad, nivel de reto).
    - Encuesta a docentes (Likert 1–5) sobre:
      - “Los desempeños son claros y observables en el aula”.

- **2.3. Coherencia de la secuencia didáctica**
  - **Definición**: Grado en que Inicio–Desarrollo–Cierre están conectados con la situación significativa y la competencia.
  - **Medición**:
    - Rúbrica con criterios:
      - Inicio vincula saberes previos y contexto
      - Desarrollo moviliza la competencia
      - Cierre incluye reflexión y transferencia

- **2.4. Uso real en aula**
  - **Definición**: Porcentaje de unidades/sesiones generadas que se implementan efectivamente en clase.
  - **Fuente**: Encuestas/reportes de docentes.
  - **Fórmula**:  
    - \( \text{\% de documentos implementados} = \frac{\# \text{documentos usados en aula}}{\# \text{documentos generados}} \times 100 \)

---

## 3. Calidad del contenido generado por IA

- **3.1. Satisfacción general del docente**
  - **Definición**: Evaluación subjetiva de la utilidad del contenido generado.
  - **Medición**:
    - Encuesta Likert 1–5 después de generar o mejorar un documento:
      - “El documento generado es útil para mi planificación”.
      - “El tiempo que me ahorra compensa el tiempo de revisión”.

- **3.2. Necesidad de edición posterior**
  - **Definición**: Cuánto tiene que corregir/modificar el docente.
  - **Métricas posibles**:
    - % de secciones aceptadas sin cambios mayores.
    - Tiempo promedio de edición por documento (autorreporte o telemetría básica).

- **3.3. Consistencia terminológica y de formato**
  - **Definición**: Cumplimiento de estructuras esperadas (tablas, formato ITEM–CONTENIDO, campos obligatorios).
  - **Medición**:
    - Validadores automáticos (scripts) que:
      - Revisan si la tabla principal tiene todas las columnas.
      - Comprueban que las tablas auxiliares respetan `| ITEM | CONTENIDO |`.
    - KPIs:
      - % de documentos que pasan validación automática sin correcciones.

- **3.4. Uso efectivo del RAG**
  - **Definición**: Medida de cuánto contenido generado hace referencia correcta a normas/competencias oficiales.
  - **Medición**:
    - Muestreo de documentos generados con RAG.
    - Revisión experta para verificar:
      - Citas coherentes a currículo, orientaciones y sesiones de capacitación.
      - Ausencia de contradicciones con el CNEB.

---

## 5. Métricas de RAG y cobertura de conocimiento

- **5.1. Cobertura de fuentes relevantes**
  - **Definición**: Porcentaje de consultas cuyo contexto RAG incluye al menos un fragmento de:
    - Currículo oficial
    - Orientaciones CNEB
    - Sesiones EF/EPT
    - Módulo de enfoque por competencias
  - **Medición**:
    - Logging de `documentos` devueltos por `RAGEducativoService.buscar_contexto_curricular`.
    - Cálculo de distribución de fuentes por consulta.

- **5.2. Profundidad del contexto**
  - **Definición**: Número medio de documentos/chunks usados para construir el contexto.
  - **Fórmula**:  
    - \( \text{profundidad media} = \frac{\sum \text{\# documentos en contexto}}{\# \text{consultas RAG}} \)

- **5.3. Relevancia percibida del contexto**
  - **Definición**: Qué tan útiles consideran los docentes las referencias a fuentes oficiales.
  - **Medición**:
    - Encuesta breve en generación RAG:
      - “El contenido estaba bien respaldado en normativa oficial” (1–5).

---
