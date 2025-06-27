import pandas as pd
from Modelo.ReglasClinicas.reglas_apoyo import obtener_componente_principal, obtener_composicion
from Modelo.MotorInferencia.Motor_inferencia import obtener_efectos

def mostrar_presentacion_inicial(notas, diagnostico, med_input):
    """Muestra los datos iniciales del paciente"""
    print(f"\n📋 DATOS DEL PACIENTE:")
    print(f"🏥 Notas clínicas: {notas}")
    print(f"🩺 Diagnóstico: {diagnostico}")
    print(f"💊 Medicamento actual: {med_input}\n")

def mostrar_seccion(titulo, ancho=80, caracter="="):
    """Muestra un título de sección centrado"""
    print(f"\n{caracter*ancho}")
    print(f" {titulo} ".center(ancho, caracter))
    print(f"{caracter*ancho}\n")

def mostrar_detalle_medicamento(titulo, composicion, nombre, detalles=None):
    """Muestra información de un medicamento de forma consistente"""
    print(f"{titulo}: {str(composicion).upper()}")
    print(f"   └─ Nombre comercial: {str(nombre).upper()}")
    if detalles:
        for detalle in detalles:
            print(f"   └─ {detalle}")

def mostrar_resultado_final(composicion_act, med_act_es, clase_act, best_n, best_s, best_j, 
                        efectos_sust, fuente_recomendacion, df_info,df_sust):
    """Muestra el resultado final optimizado con información de usos"""
    mostrar_seccion("ANÁLISIS FARMACOLÓGICO - RESULTADO", 60)
    
    # Mostrar medicamento actual
    detalles_act = [f"Clase terapéutica: {str(clase_act)}"]
    mostrar_detalle_medicamento("🧬 COMPOSICIÓN ACTUAL", composicion_act, med_act_es, detalles_act)
    
    composicion_sugerida = obtener_composicion(best_n, df_info)
    detalles_sug = [
        f"Score de compatibilidad: {best_s}",
        f"Justificación: {best_j}"
    ]

    # —> lookup del nombre comercial en español en el DataFrame de sustitutos
    nombre_comercial_es = best_n  # valor por defecto

    try:
        fila_sust = df_sust[
        df_sust["medicamento_en"].str.lower().str.contains(best_n.lower(), na=False)
    ]
        if not fila_sust.empty:
            nombre_comercial_es = str(fila_sust.iloc[0]["medicamento_principal"]).strip()
            if not nombre_comercial_es:
                nombre_comercial_es = best_n
        else:
            nombre_comercial_es = best_n
    except Exception as e:
        print(f"⚠️ Error buscando nombre comercial: {e}")
        nombre_comercial_es = best_n


    mostrar_detalle_medicamento(
        "\n✅ COMPOSICIÓN SUGERIDA",
        composicion_sugerida,
        nombre_comercial_es,   # ahora en español
        detalles_sug
    )

    # Obtener información de usos del medicamento sugerido
    usos_med = obtener_usos_medicamento(best_n, df_info)
    
    # mostrar_detalle_medicamento("\n✅ COMPOSICIÓN SUGERIDA", composicion_sugerida, best_n, detalles_sug)
    
    # Mostrar usos si están disponibles
    if usos_med and usos_med.lower() != "no disponibles":
        print(f"   └─ Usos: {usos_med}")
    
    # Mostrar origen
    origen = "Sustituto directo prioritario" if fuente_recomendacion == "sustituto_directo" else "alternativa_terapeutica"
    print(f"\n🔍 Origen: {origen}")
    
    # Mostrar efectos secundarios si existen
    if efectos_sust and efectos_sust.lower() != "no disponibles":
        print(f"\n⚠️ EFECTOS SECUNDARIOS A CONSIDERAR: {efectos_sust}")
    
    mostrar_seccion("", 60)

def obtener_usos_medicamento(nombre_medicamento, df_info):
    """Obtiene los usos de un medicamento del dataframe de información"""
    try:
        fila = df_info[df_info["medicamento"].str.lower() == nombre_medicamento.lower()]
        if not fila.empty:
            usos = fila.iloc[0].get("usos", "No disponibles")
            usos_clinicos = fila.iloc[0].get("usos_clinicos_ext", "")
            
            # Combinar ambos campos de usos si existen
            if pd.notna(usos) and pd.notna(usos_clinicos):
                return f"{usos}. {usos_clinicos}"
            elif pd.notna(usos):
                return usos
            elif pd.notna(usos_clinicos):
                return usos_clinicos
    except Exception as e:
        print(f"Error obteniendo usos para {nombre_medicamento}: {str(e)}")
    
    return "No disponibles"

def mostrar_analisis_detallado(composicion_act, med_act_es, review_act, clase_act, comp_principal, 
                            en_orden, validos_primera, alt, best_n, best_s, best_j, efectos_finales, 
                            fuente_recomendacion, df_info=None, df_sust=None):
    """Muestra el análisis detallado optimizado"""
    if df_info is None:
        raise ValueError("Error crítico: El DataFrame df_info es requerido")
    
    # Validar datos de entrada
    alt = alt if isinstance(alt, (list, tuple)) and all(len(item) == 3 for item in alt) else []
    en_orden = en_orden if isinstance(en_orden, (list, tuple)) else []
    validos_primera = validos_primera if isinstance(validos_primera, (list, tuple)) else []

    # Encabezado
    mostrar_seccion("ANÁLISIS FARMACOLÓGICO DETALLADO")
    
    # Sección 1: Información actual
    print("📊 INFORMACIÓN FARMACOLÓGICA ACTUAL\n" + "-"*40)
    detalles_actual = [
        f"Evaluación clínica: {review_act}",
        f"Clase terapéutica: {str(clase_act)}",
        f"Componente principal: {str(comp_principal)}"
    ]
    mostrar_detalle_medicamento("🧬 COMPOSICIÓN", composicion_act, med_act_es, detalles_actual)
    
    # Sección 2: Sustitutos directos
    print("\n🔄 SUSTITUTOS DIRECTOS EVALUADOS\n" + "-"*80)
    print(f"{'COMPOSICIÓN':^40} | {'SCORE':^8} | {'ESTADO':^25}")
    print("-"*80)
    
    for nombre, score, just in en_orden[:5]:
        try:
            compo = obtener_composicion(str(nombre), df_info)
            estado = "✅ VÁLIDO"
            if "❌ Alergia detectada" in str(just):
                estado = "❌ ALERGIA DETECTADA"
            elif str(just).startswith("⚠️ Información no encontrada"):
                estado = "⚠️ INFO INCOMPLETA"
            
            print(f"{str(compo).upper():<40} | {score:^8} | {estado:<25}")
            print(f"   └─ {str(just)[:80] + '...' if len(str(just)) > 80 else just}")
            print("-"*80)
        except Exception as e:
            print(f"⚠️ Error procesando {nombre}: {str(e)}")
            continue
    
    # Mejor sustituto
    if validos_primera:
        mejor_nombre, mejor_score, mejor_just = validos_primera[0]
        try:
            mejor_comp = obtener_composicion(str(mejor_nombre), df_info)
            print(f"\n✅ MEJOR SUSTITUTO DIRECTO: {str(mejor_comp).upper()}")
            print(f"   └─ Score: {mejor_score}")
            print(f"   └─ Justificación: {mejor_just}\n")
        except Exception as e:
            print(f"\n⚠️ Error con el mejor sustituto: {str(e)}\n")
    else:
        print("\n❗ No hay sustitutos directos válidos\n")
    
    # Sección 3: Alternativas
    if alt:
        print("\n🔄 ALTERNATIVAS TERAPÉUTICAS\n" + "-"*80)
        print(f"{'COMPOSICIÓN':^40} | {'SCORE':^8} | {'COMPATIBILIDAD':^25}")
        print("-"*80)
        
        for nombre_med, score_med, justificacion in alt:
            try:
                compo = obtener_composicion(str(nombre_med), df_info)
                compatibilidad = 'ALTA' if score_med > 0.7 else 'MEDIA'
                print(f"{str(compo).upper():<40} | {score_med:^8} | {compatibilidad:<25}")
                print(f"   └─ {str(justificacion)[:80] + '...' if len(str(justificacion)) > 80 else justificacion}")
                print("-"*80)
            except Exception as e:
                print(f"⚠️ Error con alternativa {nombre_med}: {str(e)}")
                continue
    
    # Recomendación final
    mostrar_seccion("RECOMENDACIÓN FINAL")
    
    try:
        compo_final = obtener_composicion(str(best_n), df_info)
        print(f"\n🏆 COMPOSICIÓN RECOMENDADA: {str(compo_final).upper()}")
        print(f"   └─ Score: {best_s}")
        # —> lookup del nombre en español
        if df_sust is not None:
            fila_final = df_sust[
                df_sust["medicamento_en"].str.lower() == best_n.lower()
            ]
            nombre_final_es = fila_final.iloc[0]["medicamento_principal"] if not fila_final.empty else best_n
        else:
            nombre_final_es = best_n
        print(f"   └─ Nombre: {str(nombre_final_es).upper()}")
        print(f"   └─ Justificación: {best_j}")


        print(f"\n📋 ORIGEN: {'Sustituto directo' if fuente_recomendacion == 'sustituto_directo' else 'alternativa_terapeutica'}")
        
        if efectos_finales and str(efectos_finales) != "No disponibles":
            print(f"\n⚠️ EFECTOS SECUNDARIOS:")
            print(f"   └─ {str(efectos_finales)}")
    except Exception as e:
        print(f"\n❌ Error mostrando recomendación final: {str(e)}")
    
    print("\n" + "="*80)