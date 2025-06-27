import pandas as pd
from deep_translator import GoogleTranslator

# === CARGAR DATASET ===
df = pd.read_csv("clinical_data.csv")

# === 1. TRADUCIR notas_clínicas COMPLETAS ===
def traducir_nota(nota):
    if pd.isna(nota) or nota.strip() == "":
        return ""
    try:
        return GoogleTranslator(source='en', target='es').translate(nota)
    except:
        return "[Error en traducción]"

print("🔄 Traduciendo notas clínicas...")
df['clinical_notes_es'] = df['clinical_notes'].apply(traducir_nota)

# === 2. TRADUCIR DIAGNOSES Y MEDICATIONS ===

# Diagnósticos
diagnosticos_unicos = set()
df['diagnoses'].dropna().str.split(',').apply(lambda lista: [diagnosticos_unicos.add(d.strip()) for d in lista])
dic_diag = {d: GoogleTranslator(source='en', target='es').translate(d) for d in diagnosticos_unicos}

# Medicamentos
medicamentos_unicos = set()
df['medications'].dropna().str.split(',').apply(lambda lista: [medicamentos_unicos.add(m.strip()) for m in lista])
dic_meds = {m: GoogleTranslator(source='en', target='es').translate(m) for m in medicamentos_unicos}

# Aplicar traducción
def traducir_lista(texto, diccionario):
    if pd.isna(texto): return texto
    traducido = [diccionario.get(item.strip(), item.strip()) for item in texto.split(',')]
    return ', '.join(traducido)

df['diagnoses_es'] = df['diagnoses'].apply(lambda x: traducir_lista(x, dic_diag))
df['medications_es'] = df['medications'].apply(lambda x: traducir_lista(x, dic_meds))

# === GUARDAR RESULTADO FINAL ===
# Crear tabla final solo con contenido traducido
df_final = df[['clinical_notes_es', 'diagnoses_es', 'medications_es']]
df_final.columns = ['notas_clinicas', 'diagnosticos', 'medicamentos']  

# Guardar nuevo archivo final
df_final.to_csv("clinical_data_traducido_final.csv", index=False)
print("✅ Archivo limpio y solo en español guardado como 'clinical_data_traducido_final.csv'")

