import pandas as pd
import time
import json
from deep_translator import GoogleTranslator

# Ruta del archivo original
archivo_entrada = "medicine_dataset_filtrado.csv"
df = pd.read_csv(archivo_entrada)

# Columnas a traducir
columnas_nombre = ["name"] + [f"substitute{i}" for i in range(5)]  # Traducir pero conservar original
columnas_solo_es = [f"sideEffect{i}" for i in range(33)] + [f"use{i}" for i in range(5)] + ["Chemical Class", "Therapeutic Class", "Habit Forming"]
columnas_originales = columnas_nombre + columnas_solo_es

# Funciones auxiliares
def cargar_diccionario(nombre_archivo):
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def guardar_diccionario(diccionario, nombre_archivo):
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=2)

def traducir_con_cache(df, col_en):
    print(f"\n🔄 Traduciendo columna: {col_en}")
    cache_file = f"traducciones_{col_en}.json"
    traducciones = cargar_diccionario(cache_file)

    valores_unicos = df[col_en].dropna().unique()
    total = len(valores_unicos)

    for i, val in enumerate(valores_unicos):
        if val in traducciones:
            continue
        try:
            traduccion = GoogleTranslator(source='en', target='es').translate(val)
        except:
            traduccion = "[Error]"
        traducciones[val] = traduccion
        guardar_diccionario(traducciones, cache_file)
        print(f"{i+1}/{total} → {val} → {traduccion}")
        time.sleep(1)
        if (i + 1) % 100 == 0:
            print("⏸ Pausa extendida para evitar bloqueo (45s)...")
            time.sleep(45)

    col_es = f"{col_en}_es"
    df[col_es] = df[col_en].map(traducciones)
    return df

# Traducir columnas según tipo
for col in columnas_originales:
    if col in columnas_nombre:
        df = traducir_con_cache(df, col)  # Conserva ambas columnas (en y _es)
    else:
        df = traducir_con_cache(df, col)
        df.drop(columns=[col], inplace=True)  # Elimina la versión en inglés

# Guardar resultado
archivo_salida = "medicine_dataset_traducidoF.csv"
df.to_csv(archivo_salida, index=False)
print(f"\n✅ Archivo final con nombres EN/ES y campos traducidos guardado como: {archivo_salida}")
