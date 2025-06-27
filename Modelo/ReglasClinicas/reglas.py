import pandas as pd
import re
from Modelo.ReglasClinicas.reglas_apoyo import contar_sintomas

def regla_alergia_por_composicion(notas, composicion, alergenos):
    """Detecta alergias basadas en composición y notas clínicas"""
    if pd.isna(notas) or pd.isna(composicion) or not alergenos:
        return None
        
    nl = notas.lower()
    cl = composicion.lower()
    
    

    # Precompilar patrones de búsqueda
    patrones_base = [
        r"alergi[ao]s?\s+a\s+",
        r"alérgic[ao]s?\s+a\s+", 
        r"reacci[óo]n\s+(?:adversa|cut[áa]nea)?\s*(?:a|con)\s+",
        r"urticaria\s+(?:por|con)\s+",
        r"hipersensibilidad\s+a\s+"
    ]
    
    # Verificar cada alérgeno
    for a in alergenos:
        a_lower = a.lower()
        
        # Verificar si el alérgeno está en la composición
        if a_lower not in cl:
            continue
            
        # Buscar patrones de alergia
        for patron in patrones_base:
            if re.search(patron + re.escape(a_lower), nl):
                return f"❌ Alergia detectada a {a}"
        
        # Búsqueda directa del término
        if re.search(r'\b' + re.escape(a_lower) + r'\b', nl):
            return f"❌ Alergia detectada a {a}"
            
    return None

def regla_sintomas_vs_efectos_secundarios(notas, efectos_det, efectos):
    """Compara síntomas con efectos secundarios potenciales"""
    if pd.isna(notas):
        return None
    
    # Combinar efectos
    texto_ef = ' '.join(filter(None, [
        str(efectos_det) if pd.notna(efectos_det) else "",
        str(efectos) if pd.notna(efectos) else ""
    ])).strip()

    if not texto_ef:
        return None

    # Preprocesar textos
    stop_words = {"y","el","la","de","a","en","con","por","para","del","al","un","una","los","las"}
    
    def extraer_palabras(texto):
        return set(w for w in re.findall(r"\w+", texto.lower()) if w not in stop_words and len(w) > 2)
    
    palabras_notas = extraer_palabras(notas)
    palabras_efectos = extraer_palabras(texto_ef)
    
    comunes = palabras_notas & palabras_efectos

    if comunes:
        return f"⚠️ Podría agravar síntomas: {', '.join(sorted(comunes))}"
    return None