import pandas as pd
import re

def obtener_componente_principal(comp):
    """Extrae el componente principal de una composición"""
    if pd.isna(comp): return ""
    return comp.lower().split('+')[0].split('(')[0].strip()

def obtener_composicion(nombre_medicamento, df_info, intentar_sustitutos=True):
    """
    Versión unificada y mejorada de obtener_composicion
    """
    # Si ya tiene paréntesis, asumimos que es la composición
    if isinstance(nombre_medicamento, str) and "(" in nombre_medicamento and ")" in nombre_medicamento:
        return nombre_medicamento
    
    # Búsqueda directa por nombre
    fila = df_info[df_info["medicamento"].str.lower() == nombre_medicamento.lower()]
    if not fila.empty:
        return fila.iloc[0]["composicion"]
    
    # Búsqueda por composición exacta
    fila_comp = df_info[df_info["composicion"].str.lower() == nombre_medicamento.lower()]
    if not fila_comp.empty:
        return fila_comp.iloc[0]["composicion"]
    
    # Si se permite buscar en sustitutos
    if intentar_sustitutos:
        try:
            sust_df = df_info.merge(pd.DataFrame({'sustituto_es': [nombre_medicamento]}), 
                                  how='right', 
                                  left_on='medicamento', 
                                  right_on='sustituto_es')
            if not sust_df.empty:
                return sust_df.iloc[0]['composicion']
        except:
            pass
        
    return "Composición no encontrada"

def contar_sintomas(riesgo):
    """Cuenta el número de síntomas en un mensaje de riesgo"""
    marker = "⚠️ Podría agravar síntomas:"
    if marker not in riesgo:
        return 0
    sub = riesgo.split(marker, 1)[1]
    sintomas = [s.strip() for s in sub.split(",") if s.strip()]
    return len(sintomas)

def evaluar_clase(c1, c2):
    """Evalúa si dos clases terapéuticas son iguales"""
    return isinstance(c1, str) and isinstance(c2, str) and c1.strip().lower() == c2.strip().lower()

def obtener_nombre_espanol(nombre_en, map_es_dict):
    """Obtiene el nombre en español de un medicamento"""
    return map_es_dict.get(nombre_en.lower(), nombre_en)