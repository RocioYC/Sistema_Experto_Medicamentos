import pandas as pd
import unicodedata
import os
import re

# Cargar el dataset unificado
df = pd.read_csv(r"C:\Users\rocio\Documents\CICLO X\001 INTELIGENCIA ARTIFICIAL\PROYECTO DE SISTEMAS EXPERTO\Proyecto_Medicamentos_Sustitutos\Modelo\BaseConocimiento\medicamentos_info.csv")

# Función para normalizar texto
def normalizar(texto):
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    return texto

# Lista para componentes únicos
componentes_unicos = set()

# Expresión regular para detectar nombres válidos (palabras con letras, guiones o números dentro del nombre)
patron_valido = re.compile(r"^[a-záéíóúñ]+[\w\- ]*[a-záéíóúñ]$", re.IGNORECASE)

# Procesar la columna "composicion"
for comp in df["composicion"].dropna():
    comp = normalizar(comp)
    comp = comp.replace(",", "+").replace(";", "+").replace("/", "+")
    partes = comp.split("+")
    for parte in partes:
        nombre = parte.strip().split("(")[0].strip()
        if patron_valido.match(nombre) and not any(char.isdigit() for char in nombre):
            componentes_unicos.add(nombre)

# Crear DataFrame limpio
df_componentes = pd.DataFrame(sorted(componentes_unicos), columns=["posibles_alergenos"])

# Guardar el archivo
nombre_archivo = "posibles_alergenos.csv"
ruta_carpeta = r"C:\Users\rocio\Documents\CICLO X\001 INTELIGENCIA ARTIFICIAL\PROYECTO DE SISTEMAS EXPERTO\Proyecto_Medicamentos_Sustitutos\Modelo\ReglasClinicas"
os.makedirs(ruta_carpeta, exist_ok=True)

ruta_guardado = os.path.join(ruta_carpeta, nombre_archivo)
df_componentes.to_csv(ruta_guardado, index=False)

print(f"✅ Se extrajeron {len(df_componentes)} nombres únicos de componentes.")
print(f"📁 Guardado en: {ruta_guardado}")
