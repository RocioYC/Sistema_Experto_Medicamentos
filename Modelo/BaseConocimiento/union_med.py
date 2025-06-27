import pandas as pd
import os

# Crear carpeta si no existe
output_folder = r"C:\Users\rocio\Documents\CICLO X\001 INTELIGENCIA ARTIFICIAL\PROYECTO DE SISTEMAS EXPERTO\Proyecto_Medicamentos_Sustitutos\Modelo\BaseConocimiento"
os.makedirs(output_folder, exist_ok=True)

# Cargar archivos base
df_drug = pd.read_csv(r"C:\Users\rocio\Documents\CICLO X\001 INTELIGENCIA ARTIFICIAL\PROYECTO DE SISTEMAS EXPERTO\Proyecto_Medicamentos_Sustitutos\Modelo\dataset\drug_data.csv")
df_medicine = pd.read_csv(r"C:\Users\rocio\Documents\CICLO X\001 INTELIGENCIA ARTIFICIAL\PROYECTO DE SISTEMAS EXPERTO\Proyecto_Medicamentos_Sustitutos\Modelo\dataset\medicine_data_limpio.csv")

# Unificar columna clave
df_drug.rename(columns={"nombre_medicamento": "medicamento"}, inplace=True)
df_medicine.rename(columns={"name": "medicamento"}, inplace=True)

# Unir los datos por medicamento
df_info = pd.merge(df_drug, df_medicine, on="medicamento", how="outer")

# Agrupar los efectos secundarios extendidos
efectos_cols = [col for col in df_info.columns if "sideEffect" in col]
df_info["efectos_secundarios_detallados"] = df_info[efectos_cols].apply(
    lambda row: ', '.join([str(val) for val in row if pd.notnull(val)]), axis=1
)

# Agrupar los usos clínicos extendidos
usos_cols = [col for col in df_info.columns if "use" in col and "_es" in col]
df_info["usos_clinicos_ext"] = df_info[usos_cols].apply(
    lambda row: ', '.join([str(val) for val in row if pd.notnull(val)]), axis=1
)

# Seleccionar columnas limpias
df_final = df_info[[ 
    "medicamento",
    "composicion",
    "usos",
    "efectos_secundarios",
    "review_excelente",
    "efectos_secundarios_detallados",
    "usos_clinicos_ext",
    "Chemical Class_es",
    "Therapeutic Class_es"
]]

df_final.rename(columns={
    "Chemical Class_es": "clase quimica",
    "Therapeutic Class_es": "clase terapeutica"
}, inplace=True)

# 🚨 Eliminar filas sin composición
df_final = df_final[df_final["composicion"].notna() & (df_final["composicion"].str.strip() != "")]

# Guardar CSV limpio y seguro
df_final.to_csv(os.path.join(output_folder, "medicamentos_info.csv"), index=False)
print("✅ Archivo 'medicamentos_info.csv' generado sin registros peligrosos (sin composición).")
