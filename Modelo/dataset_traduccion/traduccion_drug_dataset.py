import pandas as pd
import time
from deep_translator import GoogleTranslator

# Cargar el archivo
df = pd.read_csv("drug_dataset.csv")

# Función para traducir valores únicos con pausa
def traducir_columna(df, columna_original, nuevo_nombre):
    print(f"🔄 Traduciendo columna: {columna_original}")
    valores_unicos = df[columna_original].dropna().unique()#Extrae los valores únicos  de la columna original, para no traducir repeticiones
    traducciones = {}#Inicializa un diccionario vacío para almacenar las traducciones
    for idx, val in enumerate(valores_unicos):
        try:
            traduccion = GoogleTranslator(source='en', target='es').translate(val)
        except:
            traduccion = "[Error]"
        traducciones[val] = traduccion #Guarda la traducción en el diccionario para ese valor específico
        print(f"{idx + 1}/{len(valores_unicos)} → {val} → {traduccion}")
        time.sleep(3)
    df[nuevo_nombre] = df[columna_original].map(traducciones)
    return df


# Traducir columnas clave
df = traducir_columna(df, "Composition", "composicion")
df = traducir_columna(df, "Uses", "usos")
df = traducir_columna(df, "Side_effects", "efectos_secundarios")

# Armar dataframe final
df_final = df[[
    "Medicine Name", "composicion", "usos", "efectos_secundarios", "Excellent Review %"
]]
df_final.columns = [
    "nombre_medicamento", "composicion", "usos", "efectos_secundarios", "review_excelente"
]

# Guardar
df_final.to_csv("drug_dataset_traducido.csv", index=False)
print("✅ Archivo guardado como 'drug_dataset_traducido.csv'")
