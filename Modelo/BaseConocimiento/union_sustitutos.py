import pandas as pd
import os

# Crear carpeta si no existe
output_folder = r"C:\Users\rocio\Documents\CICLO X\001 INTELIGENCIA ARTIFICIAL\PROYECTO DE SISTEMAS EXPERTO\Proyecto_Medicamentos_Sustitutos\Modelo\BaseConocimiento"
os.makedirs(output_folder, exist_ok=True)

# Cargar MEDICINE_DATA traducido (ya con columnas *_es)
df_medicine = pd.read_csv(r"C:\Users\rocio\Documents\CICLO X\001 INTELIGENCIA ARTIFICIAL\PROYECTO DE SISTEMAS EXPERTO\Proyecto_Medicamentos_Sustitutos\Modelo\dataset\medicine_data_limpio.csv")

# Renombrar nombre principal
df_medicine.rename(columns={
    "name": "medicamento_en",
    "name_es": "medicamento_principal"
}, inplace=True)

# Seleccionar columnas de sustitutos en inglés y español
sustituto_en_cols = [f"substitute{i}" for i in range(5)]
sustituto_es_cols = [f"substitute{i}_es" for i in range(5)]

# Construir el DataFrame final con ambas versiones
df_sustitutos = df_medicine[["medicamento_en", "medicamento_principal"] + sustituto_en_cols + sustituto_es_cols].copy()

# Renombrar columnas para mayor claridad
df_sustitutos.rename(columns={
    "substitute0": "sustituto1_en",
    "substitute1": "sustituto2_en",
    "substitute2": "sustituto3_en",
    "substitute3": "sustituto4_en",
    "substitute4": "sustituto5_en",
    "substitute0_es": "sustituto1_es",
    "substitute1_es": "sustituto2_es",
    "substitute2_es": "sustituto3_es",
    "substitute3_es": "sustituto4_es",
    "substitute4_es": "sustituto5_es"
}, inplace=True)

# Guardar archivo
df_sustitutos.to_csv(os.path.join(output_folder, "sustitutos_medicamentos.csv"), index=False)

print("✅ Archivo 'sustitutos_medicamentos.csv' generado con sustitutos en español e inglés.")
