import os
import pandas as pd
from pathlib import Path

def configurar_rutas():
    """Configura las rutas de los archivos CSV con verificación de existencia"""
    try:
        # Obtener ruta base del proyecto (sube un nivel desde la carpeta Vista)
        ruta_base = Path(__file__).resolve().parent.parent
        
        # Definir rutas con pathlib (más robusto que os.path)
        rutas = {
            'info': ruta_base / "Modelo" / "BaseConocimiento" / "medicamentos_info.csv",
            'sustitutos': ruta_base / "Modelo" / "BaseConocimiento" / "sustitutos_medicamentos.csv",
            'alergenos': ruta_base / "Modelo" / "ReglasClinicas" / "posibles_alergenos.csv",
            'clinical': ruta_base / "Modelo" / "01Hechos" / "clinical_data.csv"
        }
        
        # Verificar que los archivos existan
        for nombre, ruta in rutas.items():
            if not ruta.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {ruta}")
                
        return rutas
        
    except Exception as e:
        print(f"❌ Error configurando rutas: {str(e)}")
        # Mostrar estructura de carpetas actual
        print("\nEstructura ACTUAL de carpetas (según tus archivos):")
        print("📁 Proyecto_Medicamentos_Sustitutos/")
        print("├── 📁 Modelo/")
        print("│   ├── 📁 BaseConocimiento/")
        print("│   │   ├── medicamentos_info.csv")
        print("│   │   └── sustitutos_medicamentos.csv")
        print("│   ├── 📁 ReglasClinicas/")
        print("│   │   └── posibles_alergenos.csv")
        print("│   └── 📁 01Hechos/")
        print("│       └── clinical_data.csv")
        print("└── ... (otras carpetas del proyecto)")
        raise

def cargar_datos(rutas):
    """Carga los datos CSV con manejo de errores"""
    try:
        return {
            'df_info': pd.read_csv(str(rutas['info'])),
            'df_sust': pd.read_csv(str(rutas['sustitutos'])),
            'df_alerg': pd.read_csv(str(rutas['alergenos'])),
            'df_clinical': pd.read_csv(str(rutas['clinical'])),
            'lista_alergenos': pd.read_csv(str(rutas['alergenos']))["posibles_alergenos"].tolist()
        }
    except Exception as e:
        print(f"❌ Error cargando datos: {str(e)}")
        raise