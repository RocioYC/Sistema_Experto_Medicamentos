
# SustituMedIA 🏥💊

**SustituMedIA** es un sistema experto de sustitución de medicamentos que, a partir de reglas clínicas y composición farmacológica, sugiere alternativas terapéuticas seguras y explicables.

---

## 📦 Distribución

Hemos generado un único ejecutable para Windows con PyInstaller. Ya no necesitas Python ni instalar dependencias: solo descarga el `.exe`.

- **Ubicación del ejecutable**:  
  `dist\SustituMedIA.exe`

---

## 🔧 Requisitos del sistema

- Windows 10 o superior (64-bit recomendado)  
- CPU con soporte SSE2  
- Opcional: antivirus que permita ejecutar aplicaciones no firmadas

---

## 🚀 Uso

1. Descarga el contenido completo del repositorio (o solo la carpeta `dist` si no vas a modificar nada).
2. Desde el **Explorador de Windows**, haz doble clic sobre:
```

dist\SustituMedIA.exe

```
3. Se abrirá la ventana gráfica con la interfaz de sustitución de medicamentos.

> **Nota**: Todos los CSV (base de conocimiento) se han empaquetado dentro del ejecutable, así que no tienes que preocuparte por rutas ni archivos adicionales.

---

## 📋 Ejemplo rápido

1. Selecciona motivo (alergia o desabastecimiento).  
2. Rellena síntomas, antecedentes, diagnóstico y nombre del medicamento.  
3. Pulsa **Procesar**.  
4. Aparecerá la **Recomendación Principal** con:  
- Composición destacada  
- Score y justificación  
- Efectos secundarios  
5. Si quieres un detalle completo, pulsa **Análisis Detallado**.

---

## 📁 Estructura del repositorio

```

Proyecto\_Medicamentos\_Sustitutos/
├── dist/                             ← Aquí están los ejecutables compilados
│   └── SustituMedIA.exe
├── Modelo/                           ← Código fuente y datos originales
│   ├── 01Hechos/
│   │   └── clinical\_data.csv
│   ├── BaseConocimiento/
│   │   ├── medicamentos\_info.csv
│   │   └── sustitutos\_medicamentos.csv
│   └── ReglasClinicas/
│       └── posibles\_alergenos.csv
├── Vista/
│   └── interfaz\_principal.py        ← Código GUI original
├── Controlador/
│   └── main.py                      ← Punto de entrada CLI (solo para desarrollo)
└── README.md                        ← Este archivo

````

---

## 🛠️ Desarrollo

Si quieres modificar o volver a compilar:

1. Clona el repositorio completo.
2. Asegúrate de tener Python 3.11+ y PyInstaller instalado:
   ```bash
   pip install pyinstaller
````

3. Desde la raíz del proyecto ejecuta:

   ```bash
   pyinstaller --onefile --windowed \
     --add-data "Modelo/01Hechos/clinical_data.csv;Modelo/01Hechos" \
     --add-data "Modelo/BaseConocimiento/medicamentos_info.csv;Modelo/BaseConocimiento" \
     --add-data "Modelo/BaseConocimiento/sustitutos_medicamentos.csv;Modelo/BaseConocimiento" \
     --add-data "Modelo/ReglasClinicas/posibles_alergenos.csv;Modelo/ReglasClinicas" \
     Vista/interfaz_principal.py
   ```
4. El nuevo `.exe` aparecerá en `dist/`.

---

¡Listo! Con esto cualquiera podrá descargar el exe y probar tu sistema sin complicaciones.
