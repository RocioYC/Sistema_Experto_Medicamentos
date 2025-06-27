import pandas as pd
import time
import json
import os
from deep_translator import GoogleTranslator

# Ruta base
ruta_base = r"C:\Users\rocio\Documents\CICLO X\001 INTELIGENCIA ARTIFICIAL\PROYECTO DE SISTEMAS EXPERTO\Proyecto_Medicamentos_Sustitutos\Modelo\dataset_traduccion"
archivo_entrada = os.path.join(ruta_base, "medicine_dataset.csv")
df = pd.read_csv(archivo_entrada, nrows=2000)

# Columnas a traducir
columnas_nombre = ["name"] + [f"substitute{i}" for i in range(5)]
columnas_solo_es = [f"sideEffect{i}" for i in range(33)] + [f"use{i}" for i in range(5)] + ["Chemical Class", "Therapeutic Class", "Habit Forming"]
columnas_originales = columnas_nombre + columnas_solo_es

# Funciones
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
    cache_file = os.path.join(ruta_base, f"traducciones_{col_en}.json")
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

# Traducir columnas
for col in columnas_originales:
    if col in columnas_nombre:
        df = traducir_con_cache(df, col)
    else:
        df = traducir_con_cache(df, col)
        df.drop(columns=[col], inplace=True)

# Guardar acumulado
archivo_salida = os.path.join(ruta_base, "medicine_dataset_traducidoF.csv")

try:
    df_existente = pd.read_csv(archivo_salida)
    df_total = pd.concat([df_existente, df], ignore_index=True).drop_duplicates()
except FileNotFoundError:
    df_total = df

df_total.to_csv(archivo_salida, index=False)
print(f"\n✅ Se guardaron {len(df)} nuevas filas. Total acumulado: {len(df_total)} registros en:\n{archivo_salida}")
