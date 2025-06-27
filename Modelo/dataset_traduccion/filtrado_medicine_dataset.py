import pandas as pd

# 1. Cargar datasets
df_250k = pd.read_csv("medicine_dataset.csv", low_memory=False)
df_drug = pd.read_csv("drug_dataset.csv")

# 2. Normalizar nombres para hacer coincidir (minúsculas y sin espacios)
nombres_drug = df_drug["Medicine Name"].str.lower().str.strip()
nombres_250k = df_250k["name"].str.lower().str.strip()

# 3. Filtrar las filas del dataset de 250k que coinciden con los nombres del drug_dataset
df_250k_filtrado = df_250k[nombres_250k.isin(nombres_drug)]

# 4. Definir columnas a eliminar (sideEffect33 a sideEffect41)
columnas_a_eliminar = [f"sideEffect{i}" for i in range(33, 42)]

# 5. Definir las columnas que sí quieres conservar
# Solo mantener sideEffect0 hasta sideEffect32
columnas_a_usar = ["name"] \
    + [f"substitute{i}" for i in range(5)] \
    + [f"sideEffect{i}" for i in range(33)] \
    + [f"use{i}" for i in range(5)] \
    + ["Chemical Class", "Therapeutic Class", "Habit Forming"]


# 6. Crear dataframe final con solo las columnas deseadas
df_250k_final = df_250k_filtrado[columnas_a_usar]

# 7. Guardar el archivo final
df_250k_final.to_csv("medicine_dataset_filtrado.csv", index=False)
print(f"✅ Dataset filtrado y reducido guardado con {len(df_250k_final)} registros.")
