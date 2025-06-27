import pandas as pd
import re
from difflib import get_close_matches
from Modelo.ReglasClinicas.reglas import regla_alergia_por_composicion, regla_sintomas_vs_efectos_secundarios
from Modelo.ReglasClinicas.reglas_apoyo import contar_sintomas, evaluar_clase, obtener_componente_principal, obtener_composicion

def obtener_pares_sustitutos(med_en, df_sust):
    """Obtiene pares de sustitutos (español, inglés) para un medicamento"""
    pairs = []
    f = df_sust[df_sust["medicamento_en"].str.lower() == med_en.lower()]
    if not f.empty:
        row = f.iloc[0]
        for i in range(1,6):
            en = row.get(f"sustituto{i}_en")
            es = row.get(f"sustituto{i}_es")
            if pd.notna(en) and pd.notna(es): 
                pairs.append((es.strip(), en.strip())) 
    return list({en:(es,en) for es,en in pairs}.values())

def score_sustituto(es, en, notas, diagnostico, clase_act, alergenos, df_info):
    """
    Calcula el score de compatibilidad para un sustituto (v2 genérico).
    Parámetros:
      es: nombre en español del medicamento
      en: nombre en inglés o input de búsqueda
      notas: notas clínicas del paciente
      diagnostico: diagnóstico principal (texto libre)
      clase_act: clase terapéutica del medicamento actual
      alergenos: lista de alérgenos del paciente
      df_info: DataFrame con información de medicamentos
    """
    # Filtrar el registro correspondiente
    f = df_info[
        (df_info["medicamento"].str.lower() == en.lower()) |
        (df_info["composicion"].str.lower().str.contains(en.lower(), na=False))
    ]
    if f.empty:
        return -5, "⚠️ Información no encontrada"

    d = f.iloc[0]
    score = 0
    just = []

    # 1) Review escalada
    rev = d.get("review_excelente", 0)
    if rev >= 80:
        score += 2; just.append("✔️ Excelente puntaje de review (≥80)")
    elif rev >= 50:
        score += 1; just.append("✔️ Buen puntaje de review (50–79)")

    # 2) Componente principal
    comp = obtener_componente_principal(d.get("composicion", ""))
    if comp:
        score += 3; just.append("✔️ Mismo componente principal")

    # 3) Clase terapéutica
    if evaluar_clase(clase_act, d.get("clase terapeutica", "")):
        score += 2; just.append("✔️ Misma clase terapéutica")

    # 4) Clase química genérica
    if clase_act.lower() == str(d.get("clase quimica", "")).lower():
        score += 1; just.append("✔️ Misma clase química")

    # 5) Indicación genérica según diagnóstico
    diag = diagnostico.lower() if diagnostico else ""
    usos_ext = str(d.get("usos_clinicos_ext", "")).lower()
    usos_bas = str(d.get("usos", "")).lower()
    if diag and diag in usos_ext:
        score += 2; just.append(f"✔️ Indicado específicamente para {diagnostico}")
    elif diag and diag in usos_bas:
        score += 1; just.append(f"✔️ Coincide en usos generales para {diagnostico}")

    # 6) Penalizaciones por efectos secundarios
    detalles = str(d.get("efectos_secundarios_detallados", "")).lower()
    if re.search(r"(quemadura|fotosensibilidad)", detalles):
        score -= 2; just.append("⚠️ Riesgo de reacción grave")
    elif re.search(r"(sequedad|irritaci[oó]n leve)", detalles):
        score -= 1; just.append("⚠️ Puede causar irritación leve")

    # 7) Alergia
    alerg = regla_alergia_por_composicion(notas, d.get("composicion", ""), alergenos)
    if alerg:
        score -= 10; just.append(alerg)

    # 8) Normalizar a rango [0,10]
    final = max(0, min(score, 10))
    return final, ", ".join(just)

def obtener_efectos(nombre_medicamento, df_info):
    """Obtiene efectos secundarios de un medicamento"""
    fila = df_info[df_info["medicamento"].str.lower() == nombre_medicamento.lower()]
    if not fila.empty:
        efectos_raw = fila.iloc[0]["efectos_secundarios"]
        if pd.notna(efectos_raw) and efectos_raw:
            return efectos_raw
    return "No disponibles"

def procesar_medicamento_actual(med_input, df_sust, df_info):
    """Versión mejorada para captura exacta de composición"""
    def crear_mapa_nombres(df):
        map_en = {}
        map_es = {}
        for _, r in df.iterrows():
            en_name = r["medicamento_en"].lower().strip()
            es_name = r["medicamento_principal"].lower().strip()
            map_en[en_name] = en_name
            map_en[es_name] = en_name
            map_es[en_name] = es_name
        return map_en, map_es
    
    def normalizar_medicamento(texto):
        """Normaliza para comparación exacta"""
        texto = str(texto).lower()
        texto = re.sub(r'[^a-z0-9\s]', '', texto)  # Eliminar caracteres especiales
        texto = re.sub(r'\s+', ' ', texto).strip()  # Unificar espacios
        texto = re.sub(r'(\d)\s*(mg|%|ml|g)', r'\1\2', texto)  # Normalizar unidades
        return texto
    
    try:
        in_lower = normalizar_medicamento(med_input)
        map_en, map_es = crear_mapa_nombres(df_sust)

        # PRIMERO: Búsqueda exacta en composiciones
        df_info["composicion_normalizada"] = df_info["composicion"].apply(normalizar_medicamento)
        mask_exacta = df_info["composicion_normalizada"] == in_lower
        
        if mask_exacta.any():
            # Ordenar por número de componentes (priorizar fórmulas más simples)
            df_temp = df_info[mask_exacta].copy()
            df_temp["num_componentes"] = df_temp["composicion"].str.count('\+') + 1
            df_temp = df_temp.sort_values("num_componentes")
            
            fila_act = df_temp.iloc[0]
            med_act_en = fila_act["medicamento"]
            med_act_es = map_es.get(med_act_en.lower(), med_act_en)
            return extraer_datos_medicamento(fila_act, med_act_en, med_act_es)

        # SEGUNDO: Búsqueda directa en el mapa (mantener tu lógica original)
        if in_lower in map_en:
            med_act_en = map_en[in_lower]
            fila_act = df_info[df_info["medicamento"].str.lower()==med_act_en].iloc[0]
            med_act_es = map_es.get(med_act_en, med_act_en)
            return extraer_datos_medicamento(fila_act, med_act_en, med_act_es)

        # TERCERO: Búsqueda por palabras clave mejorada
        def buscar_por_palabras_clave_mejorada(in_lower, df_info):
            """Búsqueda que prioriza fórmulas más simples"""
            toks = re.findall(r"\w+", in_lower)
            stop = {"mg","pp","p","de","la","el","en","crema","gel","tableta","capsula","%","pv"}
            kws = [t for t in toks if t not in stop]
            
            if not kws:
                return None
            
            mask = pd.Series(True, index=df_info.index)
            for k in kws:
                pat = rf'\b{re.escape(k)}\b'
                mask &= (
                    df_info["medicamento"].str.lower().str.contains(pat, na=False) |
                    df_info["composicion"].str.lower().str.contains(pat, na=False))
            
            if mask.any():
                # Ordenar por número de componentes
                df_temp = df_info[mask].copy()
                df_temp["num_componentes"] = df_temp["composicion"].str.count('\+') + 1
                df_temp = df_temp.sort_values("num_componentes")
                
                fila_act = df_temp.iloc[0]
                med_act_en = fila_act["medicamento"]
                return fila_act, med_act_en, med_act_en  # Asumir nombre en inglés
            
            return None

        resultados = buscar_por_palabras_clave_mejorada(in_lower, df_info)
        if resultados:
            fila_act, med_act_en, med_act_es = resultados
            return extraer_datos_medicamento(fila_act, med_act_en, med_act_es)

        # CUARTO: Búsqueda aproximada (mantener tu lógica original)
        resultados = buscar_aproximado(in_lower, df_info, map_es)
        if resultados:
            fila_act, med_act_en, med_act_es = resultados
            return extraer_datos_medicamento(fila_act, med_act_en, med_act_es)

    except Exception as e:
        print(f"Error procesando medicamento: {str(e)}")
    
    return None, None, None, None, None, None

def extraer_datos_medicamento(fila_act, med_act_en, med_act_es):
    """Extrae los datos comunes de un medicamento"""
    clase_act = fila_act.get("clase terapeutica", "")
    review_act = fila_act["review_excelente"]
    composicion_act = fila_act.get("composicion", "")
    comp_principal = obtener_componente_principal(composicion_act)
    return med_act_en, med_act_es, clase_act, review_act, composicion_act, comp_principal

def buscar_por_palabras_clave(in_lower, df_info):
    """Búsqueda por palabras clave en nombre o composición"""
    toks = re.findall(r"\w+", in_lower)
    stop = {"mg","pp","p","de","la","el","en","crema","gel","tableta","capsula","%"}
    kws = [t for t in toks if t not in stop]
    
    if not kws:
        return None
    
    mask = pd.Series(True, index=df_info.index)
    for k in kws:
        pat = rf"\b{re.escape(k)}\b"
        mask &= (
            df_info["medicamento"].str.lower().str.contains(pat, na=False) |
            df_info["composicion"].str.lower().str.contains(pat, na=False)
        )
    
    if mask.any():
        fila_act = df_info[mask].iloc[0]
        med_act_en = fila_act["medicamento"]
        med_act_es = med_act_en  # Asumimos nombre en inglés si no está en el mapa
        return fila_act, med_act_en, med_act_es
    
    return None

def buscar_aproximado(in_lower, df_info, map_es):
    """Búsqueda aproximada por similitud"""
    matches = get_close_matches(in_lower, df_info["medicamento"].str.lower(), n=1, cutoff=0.6)
    if matches:
        fila_act = df_info[df_info["medicamento"].str.lower()==matches[0]].iloc[0]
        med_act_en = fila_act["medicamento"]
        med_act_es = map_es.get(med_act_en.lower(), med_act_en)
        return fila_act, med_act_en, med_act_es
    return None

def normalizar_texto(texto):
    """Normaliza texto para búsquedas (quita tildes, mayúsculas, etc.)"""
    if pd.isna(texto):
        return ""
    
    # Convertir a minúsculas y quitar tildes
    texto = texto.lower()
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n'
    }
    for orig, repl in reemplazos.items():
        texto = texto.replace(orig, repl)
    
    # Eliminar caracteres especiales y múltiples espacios
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto

def buscar_alternativas(clase_act, diagnostico, fila_act, med_act_en, sust_pairs, df_info, notas, lista_alergenos):
    """Busca alternativas terapéuticas compatibles con prioridad en diagnóstico"""
    # 1. Primero buscar medicamentos específicos para el diagnóstico (aunque no sean de la misma clase)
    alternativas = []
    
    if not pd.isna(diagnostico):
        diag_norm = normalizar_texto(diagnostico)
        
        # Buscar en todos los medicamentos, no solo los de la misma clase
        mask_diag = (
            df_info["usos"].apply(normalizar_texto).str.contains(diag_norm, na=False) | 
            df_info["usos_clinicos_ext"].apply(normalizar_texto).str.contains(diag_norm, na=False)
        )
        
        cand_diag = df_info[mask_diag]
        
        # Excluir medicamentos ya considerados
        usados = {med_act_en.lower()} | {es_name.lower() for es_name, _ in sust_pairs}
        cand_diag = cand_diag[~cand_diag["medicamento"].str.lower().isin(usados)]
        
        # Filtrar por alergenos si existen
        if lista_alergenos:
            patient_al = [a.lower() for a in lista_alergenos if a.lower() in notas.lower()]
            if patient_al:
                mask_ok = pd.Series(True, index=cand_diag.index)
                for a in patient_al:
                    mask_ok &= ~cand_diag["composicion"].str.lower().str.contains(a, na=False)
                cand_diag = cand_diag[mask_ok]
        
        # Evaluar y agregar alternativas específicas para el diagnóstico
        for row in cand_diag.head(10).itertuples():
            enm = row.medicamento
            sc, js = score_sustituto(enm, enm, notas, diagnostico, clase_act, lista_alergenos, df_info)
            alternativas.append((enm, sc, js, "diagnóstico"))
    
    # 2. Si no encontramos por diagnóstico o necesitamos más opciones, buscar por clase terapéutica
    if clase_act and not pd.isna(clase_act):
        cand_clase = df_info[df_info["clase terapeutica"].str.lower() == clase_act.lower()]
        
        # Excluir medicamentos ya considerados
        usados = {med_act_en.lower()} | {es_name.lower() for es_name, _ in sust_pairs} | {a[0].lower() for a in alternativas}
        cand_clase = cand_clase[~cand_clase["medicamento"].str.lower().isin(usados)]
        
        # Filtrar por usos clínicos similares al medicamento actual
        uso_str = (fila_act.get("usos", "") or fila_act.get("usos_clinicos_ext", "") or "")
        uso_norm = normalizar_texto(uso_str)
        uso_toks = re.findall(r"\w+", uso_norm)
        
        if uso_toks:
            mask_u = pd.Series(False, index=cand_clase.index)
            for t in uso_toks:
                mask_u |= cand_clase["usos"].apply(normalizar_texto).str.contains(t, na=False)
                mask_u |= cand_clase["usos_clinicos_ext"].apply(normalizar_texto).str.contains(t, na=False)
            cand_clase = cand_clase[mask_u]
        
        # Filtrar por alergenos si existen
        if lista_alergenos:
            patient_al = [a.lower() for a in lista_alergenos if a.lower() in notas.lower()]
            if patient_al:
                mask_ok = pd.Series(True, index=cand_clase.index)
                for a in patient_al:
                    mask_ok &= ~cand_clase["composicion"].str.lower().str.contains(a, na=False)
                cand_clase = cand_clase[mask_ok]
        
        # Evaluar y agregar alternativas de la misma clase terapéutica
        for row in cand_clase.head(5).itertuples():
            enm = row.medicamento
            sc, js = score_sustituto(enm, enm, notas, diagnostico, clase_act, lista_alergenos, df_info)
            alternativas.append((enm, sc, js, "clase terapéutica"))
    
    # Ordenar todas las alternativas por score (priorizando las de diagnóstico)
    alternativas_ordenadas = sorted(
        alternativas, 
        key=lambda x: (
            x[1],  # Score
            0 if x[3] == "diagnóstico" else 1,  # Prioridad a diagnóstico
            -contar_sintomas(x[2])  # Menos efectos secundarios
        ), 
        reverse=True
    )
    
    # Devolver solo los datos necesarios (nombre, score, justificación)
    return [(a[0], a[1], a[2]) for a in alternativas_ordenadas]


######################################################################################
def capturar_composicion_exacta(med_input, diagnostico, df_info):
    """
    Captura la composición exacta priorizando:
    1. Coincidencia exacta con la composición simple
    2. Diagnóstico para confirmar relevancia clínica
    """
    # Normalización robusta
    def normalizar(texto):
        texto = str(texto).lower()
        texto = re.sub(r'[^a-z0-9\s]', '', texto)  # Eliminar caracteres especiales
        texto = re.sub(r'\s+', ' ', texto).strip()  # Unificar espacios
        texto = re.sub(r'(\d)\s*(mg|%|ml|g)', r'\1\2', texto)  # Normalizar unidades
        return texto

    med_buscado = normalizar(med_input)
    diag_norm = normalizar(diagnostico) if diagnostico else ""

    # 1. Buscar coincidencia EXACTA en composición
    df_info["composicion_normalizada"] = df_info["composicion"].apply(normalizar)
    mask_exacta = df_info["composicion_normalizada"] == med_buscado
    
    # Si encontramos resultados exactos
    if mask_exacta.any():
        candidatos = df_info[mask_exacta].copy()
        
        # Priorizar por diagnóstico si hay múltiples coincidencias exactas
        if len(candidatos) > 1 and diag_norm:
            candidatos["relevancia"] = candidatos.apply(
                lambda row: (
                    2 if diag_norm in normalizar(row.get("usos", "") + row.get("usos_clinicos_ext", "")) else
                    1 if any(sin in normalizar(row.get("usos", "") + row.get("usos_clinicos_ext", "")) 
                           for sin in obtener_sinonimos_diagnostico(diagnostico)) else 0
                ),
                axis=1
            )
            candidatos = candidatos.sort_values("relevancia", ascending=False)
        
        return candidatos.iloc[0]["composicion"]  # Devuelve la composición exacta

    # 2. Si no hay coincidencia exacta, buscar por componente principal
    componente_principal = med_buscado.split()[0]  # Extrae "amoxicilina" de "amoxicilina500mg"
    mask_componente = df_info["composicion_normalizada"].str.contains(componente_principal, regex=False)
    
    if mask_componente.any():
        candidatos = df_info[mask_componente].copy()
        
        # Priorizar formulaciones más simples (menos componentes)
        candidatos["num_componentes"] = candidatos["composicion"].str.count('\+') + 1
        candidatos = candidatos.sort_values("num_componentes")
        
        # Filtrar por diagnóstico si está disponible
        if diag_norm:
            candidatos["relevancia"] = candidatos.apply(
                lambda row: calcular_relevancia_diagnostico(row, diag_norm),
                axis=1
            )
            candidatos = candidatos.sort_values(["relevancia", "num_componentes"], ascending=[False, True])
        
        return candidatos.iloc[0]["composicion"]
    
    return None

def calcular_relevancia_diagnostico(row, diag_norm):
    """Calcula relevancia basada en diagnóstico"""
    usos = f"{row.get('usos', '')} {row.get('usos_clinicos_ext', '')}".lower()
    if diag_norm in usos:
        return 2
    return 1 if any(sin in usos for sin in obtener_sinonimos_diagnostico(diag_norm)) else 0

def obtener_sinonimos_diagnostico(diagnostico):
    """Sinónimos clínicos para mejor matching"""
    diag_clean = re.sub(r'[^a-z0-9\s]', '', diagnostico.lower())
    sinonimos = {
        "bronquitis": ["inflamacion bronquios", "infeccion vias respiratorias"],
        "acne": ["acne vulgar", "comedones"],
        "neumonia": ["infeccion pulmonar", "pulmonia"]
    }
    return sinonimos.get(diag_clean, [])

