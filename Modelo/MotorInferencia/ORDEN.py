import os
import sys
import re
import pandas as pd
from difflib import get_close_matches

# ---------------------------
# CONFIGURAR RUTAS
# ---------------------------
ruta_actual     = os.path.dirname(os.path.abspath(__file__))
ruta_base       = os.path.abspath(os.path.join(ruta_actual, ".."))
ruta_info       = os.path.join(ruta_base, "BaseConocimiento", "medicamentos_info.csv")
ruta_sustitutos = os.path.join(ruta_base, "BaseConocimiento", "sustitutos_medicamentos.csv")
ruta_alergenos  = os.path.join(ruta_base, "ReglasClinicas", "posibles_alergenos.csv")
ruta_clinical   = os.path.join(ruta_base, "01Hechos", "clinical_data.csv")  # Nueva ruta añadida

# ---------------------------
# CARGAR DATOS
# ---------------------------
_df_info        = pd.read_csv(ruta_info)
df_sust         = pd.read_csv(ruta_sustitutos)
df_alerg        = pd.read_csv(ruta_alergenos)
df_clinical     = pd.read_csv(ruta_clinical)  # Cargar datos clínicos
lista_alergenos = df_alerg["posibles_alergenos"].tolist()

# ---------------------------
# REGLAS CLÍNICAS
# ---------------------------

def regla_alergia_por_composicion(notas, composicion, alergenos):
    if pd.isna(notas) or pd.isna(composicion):
        return None
        
    nl = notas.lower()
    cl = composicion.lower()
    
    # Lista ampliada de patrones
    patrones = [
        "alergia a", "alérgico a", "alergia previa a", "reacción a",
        "alergia con", "hipersensibilidad a", "presentó urticaria con",
        "es alérgico a", "menciona que es alérgico a", "refiere alergia a",
        "alergia", "alérgico", "hipersensibilidad", "reacción adversa", 
        "intolerancia", "reacción cutánea", "urticaria por"
    ]
    
    # Extraer posibles menciones de alergias
    alergias_mencionadas = []
    for a in alergenos:
        a_lower = a.lower()
        
        # 1. Verificar si el alérgeno aparece directamente mencionado con algún patrón
        for p in patrones:
            if f"{p} {a_lower}" in nl:
                # Verificar si el alérgeno o alguna parte está en la composición
                if a_lower in cl or any(parte in cl for parte in a_lower.split()):
                    return f"❌ Alergia detectada a {a}"
        
        # 2. Verificar si el alérgeno aparece solo como palabra en notas y en composición
        if re.search(r'\b' + re.escape(a_lower) + r'\b', nl) and a_lower in cl:
            return f"❌ Alergia detectada a {a}"
            
    return None


def regla_sintomas_vs_efectos_secundarios(notas, efectos_det, efectos):
    #   notas: texto libre con los síntomas o quejas del paciente.
    # efectos_det: efectos secundarios detallados 
    # efectos: efectos secundarios generales o resumidos

    if pd.isna(notas): #Si las notas están vacías o son NaN (no disponibles) = Termina
        return None
    
    texto_ef = '' #Cadena llamada texto_ef contiene todos los efectos secundarios disponibles
    if pd.notna(efectos_det): texto_ef += efectos_det + ' '
    if pd.notna(efectos): texto_ef += efectos

    #Si al final no se encontró ningún efecto secundario = No se analiza
    if not texto_ef.strip(): return None

    #Se define un conjunto de "stopwords" / no aportan significado relevante
    stop = {"y","el","la","de","a","en","con","por","para","del","al","un","una","los","las"}
    # Estas se eliminarán para enfocar el análisis solo en los términos importantes (dolor, fiebre, vómito, etc.).

    tn = set(w for w in re.findall(r"\w+", notas.lower()) if w not in stop) #Se extraen todas las palabras de las notas clínicas
    te = set(w for w in re.findall(r"\w+", texto_ef.lower()) if w not in stop) # Se extraen todas las palabras efectos secundarios
    
    #Se calcula la intersección de palabras entre síntomas (tn) y efectos secundarios (te).
    comunes = tn & te

    if comunes:
        sintomas = ", ".join(sorted(comunes)) #Las ordena y las convierte en un string separado por comas
        return f"⚠️ Podría agravar síntomas: {sintomas}" # Devuelve una advertencia textual mostrando los síntomas que podrían agravarse
    return None



def contar_sintomas(riesgo):
    #RECIBE UN PARÁMETRO riesgo, que es un texto (string)--> "⚠️ Podría agravar síntomas: vómito, mareo"
    marker = "⚠️ Podría agravar síntomas:" #frase clave que indica el inicio de la lista de síntomas
    if marker not in riesgo: #no está dentro del texto recibido
        return 0
    
    sub = riesgo.split(marker, 1)[1] #Divide el texto en 2 partes usando marker como separador
    # Separamos los síntomas usando , Luego eliminamos espacios con .strip()
    sintomas = [s.strip() for s in sub.split(",") if s.strip()]
    return len(sintomas) #Devuelve la cantidad de síntomas encontrados

def evaluar_clase(c1, c2):
    # define una 2 CLASES TERÁPEUTICAS  c1 y c2
    # isinstance(n, str) = Asegura que ambos valores sean cadenas de texto
    return isinstance(c1, str) and isinstance(c2, str) and c1.strip().lower() == c2.strip().lower() #devuelve True o False

def obtener_componente_principal(comp):
    if pd.isna(comp): return "" #Si comp es nulo o no disponible = devuelve una cadena vacía.

    #Separa el texto por el símbolo + (que indica múltiples compuestos)
    #Ahora separa por el paréntesis que contiene la dosis
    #"Amoxicilina (500mg) + Ácido Clavulánico (125mg)" ->>>	"amoxicilina"
    return comp.lower().split('+')[0].split('(')[0].strip() 

# ---------------------------
# MOTOR DE SUSTITUTOS
# ---------------------------
def obtener_pares_sustitutos(med_en, df_sust):
    #med_en: nombre del medicamento actual en inglés
    #df_sust: Dataset que contiene las columnas medicamento_en, sustituto1_en, sustituto1_es, ..., sustituto5_en, sustituto5_es.
    pairs = [] #Se usará para almacenar los pares (español, inglés) de los sustitutos encontrados.

    f = df_sust[df_sust["medicamento_en"].str.lower() == med_en.lower()] # FILTAR "medicamento_en" ==  med_en

    if not f.empty: #Si se encontró al menos una fila que coincide
        row = f.iloc[0] #toma la primera fila
        for i in range(1,6): #obtener el valor de las columnas
            en = row.get(f"sustituto{i}_en")
            es = row.get(f"sustituto{i}_es")

            if pd.notna(en) and pd.notna(es): 
                pairs.append((es.strip(), en.strip())) 
    return list({en:(es,en) for es,en in pairs}.values()) #Se construye un diccionario y elimina duplicados

def score_sustituto(es, en, notas, diagnostico, clase_act, alergenos):
# es: nombre del sustituto en español (solo para mostrar).
# en: nombre del sustituto en inglés (clave para buscar en la base).
# notas: síntomas del paciente (texto libre).
# diagnostico: diagnóstico del paciente.
# clase_act: clase terapéutica del medicamento original.
# alergenos: lista de alergias del paciente.

    # 1. Búsqueda del medicamento en el dataset:
    f = _df_info[
        (_df_info["medicamento"].str.lower() == en.lower()) |
        (_df_info["composicion"].str.lower().str.contains(en.lower(), na=False))
    ]
    if f.empty: # Si no se encontró información del medicamento
        return -5, "⚠️ Información no encontrada"
    d = f.iloc[0] #Toma la primera fila encontrada (d) como fuente de datos del sustituto

    #   Inicializa el puntaje en 0.
    # just será una lista de textos explicativos que se irán sumando
    score, just = 0, []
# ------------------------------------------------------------------------------------------
# ✅ CRITERIOS DE EVALUACIÓN -----------------------------------------
# ------------------------------------------------------------------------------------------
    if d["review_excelente"] >= 50:
        score += 1; just.append("✔️ Buen puntaje de review")
    
    comp = obtener_componente_principal(d.get("composicion", ""))
    if comp:
        score += 3; just.append("✔️ Mismo componente principal")
    
    if evaluar_clase(clase_act, d.get("clase terapeutica", "")):
        score += 2; just.append("✔️ Misma clase terapéutica")
    
    # Verifica si el diagnóstico del paciente aparece dentro de los usos del medicamento
    indicaciones = str(d.get("usos", "") or "") + " " + str(d.get("usos_clinicos_ext", "") or "")
    if not pd.isna(diagnostico) and diagnostico.lower() in indicaciones.lower():
        score += 2  # Mayor peso por la indicación directa
        just.append(f"✔️ Indicado específicamente para {diagnostico}")
    
    # Por cada síntoma coincidente, se resta 1 punto.
    riesgo = regla_sintomas_vs_efectos_secundarios(
        notas,
        d.get("efectos_secundarios_detallados", ""),
        d.get("efectos_secundarios", "")
    )
    if riesgo:
        n = contar_sintomas(riesgo)
        score -= n
        just.append(riesgo)

    # Si detecta alergia, se restan 10 puntos (criterio grave).
    alerg = regla_alergia_por_composicion(notas,d.get("composicion", ""),alergenos)
    if alerg:
        score -= 10; just.append(alerg)
    return score, ", ".join(just)

# ---------------------------
# PERFIL DEL PACIENTE
# ---------------------------
# Usar el primer registro del CSV de datos clínicos
if df_clinical.empty:
    print("❌ No hay datos clínicos disponibles.")
    sys.exit()

# Obtener datos del primer registro en el CSV
registro_paciente = df_clinical.iloc[0]
notas = registro_paciente["notas_clinicas"]
med_input = registro_paciente["medicamentos"]
diagnostico = registro_paciente["diagnosticos"]

print(f"\n📋 DATOS DEL PACIENTE:")
print(f"🏥 Notas clínicas: {notas}")
print(f"🩺 Diagnóstico: {diagnostico}")
print(f"💊 Medicamento actual: {med_input}\n")

#------------------------------------------------------------
# Crea los diccionarios de mapeo entre idioma
#-----------------------------------------------------------

in_lower = med_input.lower().strip()
map_en = {}
map_es = {}  # Nuevo diccionario para mapear nombres en inglés a español
for _, r in df_sust.iterrows():
    en_name = r["medicamento_en"].lower().strip()
    es_name = r["medicamento_principal"].lower().strip()
    map_en[en_name] = en_name
    map_en[es_name] = en_name
    map_es[en_name] = es_name  # Guardar el mapeo de inglés a español

#------------------------------------------
# Busca coincidencia exacta
#---------------------------------------------

if in_lower in map_en:
    med_act_en = map_en[in_lower]
    fila_act   = _df_info[_df_info["medicamento"].str.lower()==med_act_en].iloc[0]
    # Obtener nombre en español si existe
    med_act_es = map_es.get(med_act_en, med_act_en)  # Si no existe, usar el nombre en inglés
else:
    # Si no hay coincidencia exacta: busca por palabras clave
    toks = re.findall(r"\w+", in_lower) # Divide el texto en palabras individuales

    #Elimina las stopwords médicas
    stop = {"mg","pp","p","de","la","el","en","crema","gel","tableta","capsula","%"}
    kws = [t for t in toks if t not in stop]  # Conserva solo las palabras clave (kws) para buscar.

    #Filtra el DATASET buscando esas palabras en medicamento o composición
    mask = pd.Series(True, index=_df_info.index)
    for k in kws:
        pat = rf"\b{re.escape(k)}\b"
        mask &= (
            _df_info["medicamento"].str.lower().str.contains(pat, na=False) |
            _df_info["composicion"].str.lower().str.contains(pat, na=False)
        )

    # Si encuentra alguna coincidencia Asume que ese es el medicamento buscado.
    if mask.any():
        fila_act = _df_info[mask].iloc[0]
        med_act_en = fila_act["medicamento"]

        # Buscar nombre en español
        med_act_es = map_es.get(med_act_en.lower(), med_act_en)
    
    # Si no encuentra nada: usa coincidencia aproximada
    else:
        matches = get_close_matches(in_lower, _df_info["medicamento"].str.lower(), n=1, cutoff=0.6)
        if matches:
            fila_act = _df_info[_df_info["medicamento"].str.lower()==matches[0]].iloc[0]
            med_act_en = fila_act["medicamento"]
            # Buscar nombre en español
            med_act_es = map_es.get(med_act_en.lower(), med_act_en)
        else:
            print("❌ Medicamento actual no encontrado.")
            sys.exit()

clase_act = fila_act.get("clase terapeutica", "")
review_act = fila_act["review_excelente"]
composicion_act = fila_act.get("composicion", "")
comp_principal = obtener_componente_principal(composicion_act)

# ---------------------------------------------------------------------
# EVALUAR SUSTITUTOS (primera línea)
# -------------------------------------------------------------------------
sust_pairs = obtener_pares_sustitutos(med_act_en, df_sust)
puntajes = [(es, sc, js)
        for es, en in sust_pairs
        for sc, js in [score_sustituto(es, en, notas, diagnostico, clase_act, lista_alergenos)]]

en_orden = sorted(puntajes, key=lambda x: (x[1], -contar_sintomas(x[2])), reverse=True)

omitidos_primera = {n for n, sc, js in en_orden if "⚠️ Información no encontrada" in js or "❌ Alergia detectada" in js}
validos_primera = [c for c in en_orden if c[0] not in omitidos_primera]

# Inicializar los candidatos principales
candidatos_finales = []
if validos_primera:
    candidatos_finales.extend(validos_primera)
    top_n, top_s, top_j = validos_primera[0]
else:
    # No hay candidatos válidos en primera línea
    top_n, top_s, top_j = None, -999, "Sin candidatos válidos"

# Función auxiliar para buscar nombre en español para un medicamento dado
def obtener_nombre_espanol(nombre_en, map_es_dict):
    """Busca el nombre en español de un medicamento que está en inglés"""
    return map_es_dict.get(nombre_en.lower(), nombre_en)

# -----------------------------------------------------------
# BUSCAR ALTERNATIVAS (segunda línea)
# ----------------------------------------------------------
# Preparar para búsqueda alternativa
cand = _df_info[_df_info["clase terapeutica"].str.lower() == clase_act.lower()]

# Buscar medicamentos que tengan indicación para el diagnóstico específico
if not pd.isna(diagnostico):
    diagnostico_lower = diagnostico.lower()
    mask_diag = (
        cand["usos"].str.lower().str.contains(diagnostico_lower, na=False) | 
        cand["usos_clinicos_ext"].str.lower().str.contains(diagnostico_lower, na=False)
    )
    # Si encontramos medicamentos específicos para el diagnóstico, priorizarlos
    cand_diag = cand[mask_diag]
    if not cand_diag.empty:
        cand = cand_diag
        print(f"🎯 Se priorizan medicamentos indicados específicamente para {diagnostico}")

# Continuar con la búsqueda por usos si es necesario
uso_str = (fila_act.get("usos", "") or fila_act.get("usos_clinicos_ext", "")).lower()
uso_toks = re.findall(r"\w+", uso_str)
mask_u = pd.Series(False, index=cand.index)
for t in uso_toks:
    mask_u |= cand["usos"].str.lower().str.contains(t, na=False)
    mask_u |= cand["usos_clinicos_ext"].str.lower().str.contains(t, na=False)
cand = cand[mask_u]
usados = {med_act_en.lower()} | {es_name.lower() for es_name, _ in sust_pairs}
cand = cand[~cand["medicamento"].str.lower().isin(usados)]
patient_al = [a for a in lista_alergenos if a in notas.lower()]
if patient_al:
    mask_ok = pd.Series(True, index=cand.index)
    for a in patient_al:
        mask_ok &= ~cand["composicion"].str.lower().str.contains(a, na=False)
    cand = cand[mask_ok]

alt = []
if not cand.empty:
    for row in cand.head(5).itertuples():
        enm = row.medicamento
        sc, js = score_sustituto(enm, enm, notas, diagnostico, clase_act, lista_alergenos)
        alt.append((enm, sc, js))

    alt = sorted(alt, key=lambda x: (x[1], -contar_sintomas(x[2])), reverse=True)
    candidatos_finales.extend(alt)

# ---------------------------
# DETERMINAR SUGERENCIA FINAL (aplicando regla de prioridad)
# ---------------------------
# Regla de prioridad: Si hay al menos un sustituto directo válido, se elige ese
# sin considerar los alternativos. Solo si no hay sustitutos directos válidos,
# se consideran los alternativos.

usar_alternativos = False
if validos_primera:
    # Hay al menos un sustituto directo válido, elegimos el mejor de ellos
    best_n, best_s, best_j = validos_primera[0]
    fuente_recomendacion = "primera_linea"
elif alt:
    # No hay sustitutos directos válidos, usamos los alternativos
    usar_alternativos = True
    best_n, best_s, best_j = alt[0]
    fuente_recomendacion = "alternativa"
else:
    print("❌ No se encontraron sustitutos válidos.")
    sys.exit()

# ---------------------------
# SALIDA FINAL - ENFOCADA EN COMPOSICIÓN
# ---------------------------

# Función para obtener la composición a partir del nombre
def obtener_composicion(nombre_medicamento):
    # Primero verificamos si el input ya es una composición con concentración
    if "(" in nombre_medicamento and ")" in nombre_medicamento:
        return nombre_medicamento  # Ya es una composición, la devolvemos directamente
    
    # Si no, buscamos en el DataFrame
    fila = _df_info[_df_info["medicamento"].str.lower() == nombre_medicamento.lower()]
    if not fila.empty:
        return fila.iloc[0]["composicion"]
    
    # Si no está como medicamento, verificamos si coincide con alguna composición
    fila_comp = _df_info[_df_info["composicion"].str.lower() == nombre_medicamento.lower()]
    if not fila_comp.empty:
        return fila_comp.iloc[0]["composicion"]
        
    return "Composición no encontrada"

# Función para obtener efectos secundarios
def obtener_efectos(nombre_medicamento):
    fila = _df_info[_df_info["medicamento"].str.lower() == nombre_medicamento.lower()]
    if not fila.empty:
        efectos_raw = fila.iloc[0]["efectos_secundarios"]
        if pd.notna(efectos_raw) and efectos_raw:
            return efectos_raw
    return "No disponibles"

# Imprimir encabezado con línea separadora
print("\n" + "="*60)
print(" ANÁLISIS FARMACOLÓGICO - RESULTADO ".center(60, "="))
print("="*60 + "\n")

# Información medicamento actual (BASADO EN COMPOSICIÓN)
print(f"🧬 COMPOSICIÓN ACTUAL: {composicion_act.upper()}")
print(f"   └─ Nombre comercial: {med_act_es.upper()}")
print(f"   └─ Clase terapéutica: {clase_act}")

# Información medicamento sugerido (BASADO EN COMPOSICIÓN)
composicion_sugerida = obtener_composicion(best_n)
print(f"\n✅ COMPOSICIÓN SUGERIDA: {composicion_sugerida.upper()}")
print(f"   └─ Score de compatibilidad: {best_s}")
print(f"   └─ Nombre comercial: {best_n.upper()}")
print(f"   └─ Justificación: {best_j}")

# Mostrar mensaje indicando el origen de la recomendación
if fuente_recomendacion == "primera_linea":
    print("\n🔍 Origen: Sustituto directo prioritario (misma composición o similar)")
else:
    print("\n🔍 Origen: Alternativa terapéutica (misma clase terapéutica y uso clínico)")

# Información sobre efectos secundarios del medicamento sugerido
efectos_sust = obtener_efectos(best_n)
if efectos_sust != "No disponibles":
    print(f"\n⚠️ EFECTOS SECUNDARIOS A CONSIDERAR: {efectos_sust}")

print("\n" + "="*60)

# ---------------------------
# OPCIÓN DETALLE - ENFOCADA EN COMPOSICIÓN
# ---------------------------
resp = input("¿Deseas ver el análisis farmacológico detallado? (si/no): ").strip().lower()
if resp not in ("si", "s", "yes", "y"):
    print("Proceso terminado.")
    sys.exit()

# Encabezado del análisis detallado
print("\n" + "="*80)
print(" ANÁLISIS FARMACOLÓGICO DETALLADO ".center(80, "="))
print("="*80 + "\n")

# SECCIÓN 1: INFORMACIÓN DEL MEDICAMENTO ACTUAL
print("📊 INFORMACIÓN FARMACOLÓGICA ACTUAL\n" + "-"*40)
print(f"🧬 COMPOSICIÓN: {composicion_act.upper()}")
print(f"📦 Nombre comercial: {med_act_es.upper()}")
print(f"📈 Evaluación clínica: {review_act}")
print(f"📑 Clase terapéutica: {clase_act}")
print(f"🎯 Componente principal: {comp_principal}\n")

# SECCIÓN 2: SUSTITUTOS DIRECTOS (TABLA)
print("🔄 SUSTITUTOS DIRECTOS EVALUADOS (POR COMPOSICIÓN)\n" + "-"*80)
print(f"{'COMPOSICIÓN':^40} | {'SCORE':^8} | {'ESTADO':^25}")
print("-"*80)

# Recorremos los sustitutos directos
for name, score, just in en_orden[:5]:
    # Obtener la composición - maneja tanto nombres comerciales como compuestos ya formateados
    compo = obtener_composicion(name)
    
    # Determinar estado del medicamento
    estado = "✅ VÁLIDO"
    if "❌ Alergia detectada" in just:
        estado = "❌ ALERGIA DETECTADA"
    elif just.startswith("⚠️ Información no encontrada"):
        estado = "⚠️ INFO INCOMPLETA"
    
    # Mostrar fila de la tabla
    print(f"{compo.upper():<40} | {score:^8} | {estado:<25}")
    # Mostrar justificación resumida
    just_resumida = just[:80] + "..." if len(just) > 80 else just
    print(f"   └─ {just_resumida}")
    print("-"*80)

# Mejor sustituto directo (si existe)
if validos_primera:
    mejor_nombre = validos_primera[0][0]
    mejor_comp = obtener_composicion(mejor_nombre)
    print(f"\n✅ MEJOR SUSTITUTO DIRECTO: {mejor_comp.upper()}")
    print(f"   └─ Score: {validos_primera[0][1]}")
    print(f"   └─ Justificación: {validos_primera[0][2]}\n")
else:
    print("\n❗ No se encontraron sustitutos directos válidos (sin alergias ni información faltante).\n")

# Manejo de omitidos y alternativas
omitted = []
for name, score, just in en_orden[:5]:
    if "❌ Alergia detectada" in just:
        omitted.append((name, "alergia"))
    elif just.startswith("⚠️ Información no encontrada"):
        omitted.append((name, "información no encontrada"))

if omitted:
    for name, reason in omitted:
        compo = obtener_composicion(name)
        print(f"⚠️ El medicamento con composición {compo.upper()} se omite por {reason}.\n")

# SECCIÓN 3: ALTERNATIVAS TERAPÉUTICAS
if alt:
    print("\n🔄 ALTERNATIVAS TERAPÉUTICAS (MISMA CLASE Y USO CLÍNICO)\n" + "-"*80)
    print(f"{'COMPOSICIÓN':^40} | {'SCORE':^8} | {'COMPATIBILIDAD':^25}")
    print("-"*80)
    
    for n, sc, j in alt:
        compo = obtener_composicion(n)
        print(f"{compo.upper():<40} | {sc:^8} | {'ALTA' if sc > 0.7 else 'MEDIA':<25}")
        just_resumida = j[:80] + "..." if len(j) > 80 else j
        print(f"   └─ {just_resumida}")
        print("-"*80)
    
    if not validos_primera:
        mejor_comp = obtener_composicion(alt[0][0])
        print(f"\n✅ MEJOR ALTERNATIVA TERAPÉUTICA: {mejor_comp.upper()}")
        print(f"   └─ Score: {alt[0][1]}")
        print(f"   └─ Justificación: {alt[0][2]}\n")
    else:
        print("\nℹ️ Las alternativas terapéuticas no se consideran debido a que existen sustitutos directos válidos.\n")

# SECCIÓN 4: RECOMENDACIÓN FINAL
compo_final = obtener_composicion(best_n)
print("\n" + "="*80)
print(" RECOMENDACIÓN FINAL ".center(80, "="))
print("="*80)
print(f"\n🏆 COMPOSICIÓN RECOMENDADA: {compo_final.upper()}")
print(f"   └─ Score: {best_s}")
print(f"   └─ Nombre comercial: {best_n.upper()}")
print(f"   └─ Justificación: {best_j}")

# Indicar fuente de la recomendación
print(f"\n📋 ORIGEN DE LA RECOMENDACIÓN:")
if fuente_recomendacion == "primera_linea":
    print("   └─ Sustituto directo prioritario (misma composición o similar)")
else:
    print("   └─ Alternativa terapéutica (mismo mecanismo de acción y uso clínico)")

# Efectos secundarios del sustituto recomendado
efectos_finales = obtener_efectos(best_n)
if efectos_finales != "No disponibles":
    print(f"\n⚠️ EFECTOS SECUNDARIOS A CONSIDERAR:")
    print(f"   └─ {efectos_finales}")

print("\n" + "="*80)