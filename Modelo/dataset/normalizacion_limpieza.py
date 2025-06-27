import pandas as pd
import os
import unicodedata

# Función para eliminar tildes y normalizar texto
def normalizar_texto(texto):
    if pd.isna(texto):
        return texto
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    return texto

# Función principal para limpiar y normalizar un dataset
def limpiar_dataset(nombre_archivo_entrada, columnas_clave, nombre_archivo_salida):
    # Ruta base del proyecto (sube un nivel desde dataset/)
    ruta_base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Rutas de entrada
    ruta_entrada = os.path.join(ruta_base, "dataset_traduccion", nombre_archivo_entrada)

    # Ruta de salida dependiendo del archivo
    if "clinical_data.csv" in nombre_archivo_salida:
        ruta_salida = os.path.join(ruta_base, "01Hechos", "clinical_data.csv")
    else:
        ruta_salida = os.path.join(os.path.dirname(__file__), nombre_archivo_salida)

    # Leer dataset
    df = pd.read_csv(ruta_entrada, low_memory=False)

    # 1. Normalizar todas las columnas de tipo texto,
    # pero evitar normalizar 'notas_clinicas' si es clinical_data
    for col in df.select_dtypes(include=['object']).columns:
        if "clinical_data.csv" in nombre_archivo_salida and col == "notas_clinicas":
            continue  # Mantener tildes en notas clínicas
        df[col] = df[col].apply(normalizar_texto)

    # 2. Reemplazar valores problemáticos por NaN
    df.replace(["na", "n/a", "-", ""], pd.NA, inplace=True)

    # 3. Eliminar duplicados solo si NO es clinical_data
    if "medicamentos" not in columnas_clave:
        df.drop_duplicates(subset=columnas_clave, keep='first', inplace=True)

    # 4. Guardar archivo limpio
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    df.to_csv(ruta_salida, index=False)
    return f"✅ Dataset limpio guardado en: {ruta_salida}", df.shape


# Datasets a procesar
datasets = [
    {
        "archivo_entrada": "drug_dataset_traducido.csv",
        "columnas_clave": ["nombre_medicamento"],
        "archivo_salida": "drug_data.csv"
    },
    {
        "archivo_entrada": "medicine_dataset_traducidoF.csv",
        "columnas_clave": ["name"],
        "archivo_salida": "medicine_data_limpio.csv"
    },
    {
        "archivo_entrada": "clinical_data_traducido.csv",
        "columnas_clave": ["medicamentos"],
        "archivo_salida": "clinical_data.csv"
    }
]

# Ejecutar limpieza para cada archivo
resultados = [
    limpiar_dataset(d["archivo_entrada"], d["columnas_clave"], d["archivo_salida"])
    for d in datasets
]

# Mostrar resumen final
df_resultados = pd.DataFrame(resultados, columns=["Resultado", "Forma del dataset"])
print(df_resultados)
