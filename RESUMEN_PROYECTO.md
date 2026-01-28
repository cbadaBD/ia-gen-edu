# 📋 Resumen del Proyecto - Generador Educativo AI

## ✅ Estado Actual del Proyecto

### **¿Qué Genera el Proyecto?**

El proyecto puede generar **3 tipos de contenido educativo**:

1. **📚 Programación Curricular Completa**
   - Tabla con 6 columnas (Competencia, Capacidades, Contenidos, Desempeños, Criterios, Instrumentos)
   - Competencias transversales
   - Enfoques transversales
   - Secuencia de 6 sesiones de aprendizaje
   - Formato: TXT y DOCX (guardado automáticamente en Desktop)

2. **🖼️ Imágenes Educativas**
   - Generación de imágenes usando Stable Diffusion XL
   - Basadas en descripciones de prompts
   - Visualización en la interfaz

3. **🗣️ Análisis de Comentarios**
   - Análisis de comentarios de estudiantes/docentes
   - Resumen con opiniones positivas y negativas
   - Recomendaciones
   - Formato: TXT y DOCX (guardado automáticamente en Desktop)

---

## ⚠️ Requisito para Generar Contenido

### **Necesitas Credenciales de AWS**

El proyecto usa **Amazon Bedrock** para generar contenido, por lo que necesitas:

1. **Crear archivo `.env`** en la raíz del proyecto:

```bash
cp env.example .env
```

2. **Editar `.env`** con tus credenciales AWS:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=tu_aws_access_key_id
AWS_SECRET_ACCESS_KEY=tu_aws_secret_access_key
```

3. **Verificar permisos AWS**:
   - Bedrock habilitado en tu cuenta AWS
   - Permisos IAM para usar Bedrock

---

## 🚀 Cómo Usar el Proyecto

### **1. Configurar Credenciales**

```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar con tus credenciales
nano .env  # o usa tu editor preferido
```

### **2. Ejecutar la Aplicación**

```bash
# Opción A: Usar run.py (recomendado)
python3 run.py

# Opción B: Comando directo
streamlit run src/app/app.py

# Opción C: Presionar F5 en el IDE (si está configurado)
```

### **3. Usar la Interfaz Web**

1. Abre `http://localhost:8501` en tu navegador
2. Selecciona el tab correspondiente:
   - **Tab 1**: Programación Curricular
   - **Tab 2**: Imágenes Educativas
   - **Tab 3**: Análisis de Comentarios
3. Llena el formulario y haz clic en "Generar"
4. Los archivos se guardan automáticamente en `~/Desktop/content_edu_outputs/`

---

## 📁 Ubicación de Outputs

Todos los archivos generados se guardan en:

```
~/Desktop/content_edu_outputs/
```

Ejemplos:
- `programacion_curricular_3to_secundaria.txt`
- `programacion_curricular_3to_secundaria.docx`
- `analisis_comentarios_20260116.txt`
- `analisis_comentarios_20260116.docx`

---

## ✅ Verificación Rápida

Para verificar que todo funciona:

```bash
# 1. Verificar dependencias
pip install -r requirements.txt

# 2. Verificar credenciales AWS
python3 -c "import os; print('AWS_REGION:', os.getenv('AWS_REGION', 'NO CONFIGURADO'))"

# 3. Ejecutar aplicación
python3 run.py
```

---

## 📝 Documentación Adicional

- **`CONFIGURACION_AWS.md`**: Guía detallada de configuración AWS
- **`COMO_EJECUTAR.md`**: Instrucciones de ejecución
- **`README.md`**: Documentación general del proyecto

---

**Última actualización**: 2026-01-16
