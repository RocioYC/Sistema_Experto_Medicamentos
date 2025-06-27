import sys
import pandas as pd
from os.path import dirname, abspath

# Configuración de rutas
project_dir = dirname(dirname(abspath(__file__)))
sys.path.append(project_dir)

# Importaciones
from Vista.rutas import configurar_rutas, cargar_datos
from Modelo.MotorInferencia.Motor_inferencia_Data import (
    obtener_pares_sustitutos, 
    score_sustituto, 
    obtener_efectos,
    procesar_medicamento_actual,
    buscar_alternativas
)
from Vista.presentacion_explicativa import (
    mostrar_presentacion_inicial, 
    mostrar_resultado_final, 
    mostrar_analisis_detallado
)

def verificar_datos_clinicos(df_clinical):
    """Verifica y normaliza las columnas del dataframe clínico"""
    mapeo_columnas = {
        'notas_clinicas': ['notas_clinicas', 'notas', 'clinical_notes'],
        'medicamentos': ['medicamentos', 'medicamento_actual', 'medication'],
        'diagnosticos': ['diagnosticos', 'diagnostico', 'diagnosis']
    }
    
    columnas_encontradas = {}
    
    for col_estandar, alternativas in mapeo_columnas.items():
        for alternativa in alternativas:
            if alternativa in df_clinical.columns:
                columnas_encontradas[col_estandar] = alternativa
                break
    
    if len(columnas_encontradas) != 3:
        print("\n❌ Error: Columnas requeridas no encontradas en clinical_data.csv")
        print("Se buscaron:")
        print("- Notas clínicas (puede llamarse: notas_clinicas, notas, clinical_notes)")
        print("- Medicamentos (puede llamarse: medicamentos, medicamento_actual, medication)")
        print("- Diagnosticos (puede llamarse: diagnosticos, diagnostico, diagnosis)")
        print("\nColumnas disponibles:", list(df_clinical.columns))
        return None
    
    return columnas_encontradas

def main():
    try:
        print("\n" + "="*60)
        print(" SISTEMA EXPERTO - SUSTITUCIÓN DE MEDICAMENTOS ".center(60, "="))
        print("="*60)
        
        # 1. Cargar datos
        print("\n🔍 Cargando datos...")
        rutas = configurar_rutas()
        datos = cargar_datos(rutas)
        
        # 2. Verificar datos clínicos
        if datos['df_clinical'].empty:
            print("❌ No hay datos clínicos disponibles.")
            sys.exit(1)
            
        mapeo_columnas = verificar_datos_clinicos(datos['df_clinical'])
        if not mapeo_columnas:
            sys.exit(1)
        
        # 3. Obtener datos del paciente (usando nombres de columnas correctos) (～￣▽￣)～
        paciente = datos['df_clinical'].iloc[14] 
        notas = paciente[mapeo_columnas['notas_clinicas']]
        med_input = paciente[mapeo_columnas['medicamentos']]
        diagnostico = paciente.get(mapeo_columnas['diagnosticos'], "No especificado")
        
        # 4. Mostrar presentación inicial
        mostrar_presentacion_inicial(notas, diagnostico, med_input)
        
        # 5. Procesar medicamento actual
        print("\n🔍 Procesando medicamento actual...")
        resultados = procesar_medicamento_actual(
            med_input, datos['df_sust'], datos['df_info'])
        
        med_act_en, med_act_es, clase_act, review_act, composicion_act, comp_principal = resultados
        
        if not med_act_en:
            print("❌ No se pudo identificar el medicamento actual.")
            sys.exit(1)
        
        # 6. Obtener y evaluar sustitutos
        print("🔄 Buscando sustitutos directos...")
        sust_pairs = obtener_pares_sustitutos(med_act_en, datos['df_sust'])
        
        en_orden = []
        for es_name, en_name in sust_pairs:
            score, just = score_sustituto(
                es_name, en_name, notas, 
                diagnostico, clase_act, 
                datos['lista_alergenos'], datos['df_info']
            )
            en_orden.append((en_name, score, just))
        
        # Ordenar por score (mayor primero)
        en_orden.sort(key=lambda x: x[1], reverse=True)
        
        # Filtrar sustitutos válidos
        validos_primera = [
            (name, score, just) for name, score, just in en_orden
            if "❌ Alergia detectada" not in just 
            and "⚠️ Información no encontrada" not in just
        ]
        
        # 7. Buscar alternativas si no hay sustitutos válidos
        if not validos_primera:
            print("⚠️ No hay sustitutos directos válidos, buscando alternativas...")
            fila_act = datos['df_info'][datos['df_info']["medicamento"].str.lower() == med_act_en.lower()].iloc[0]
            alt = buscar_alternativas(
                clase_act, diagnostico, fila_act, 
                med_act_en, sust_pairs, datos['df_info'], 
                notas, datos['lista_alergenos']
            )
        else:
            alt = []
        
        # 8. Determinar mejor recomendación
        if validos_primera:
            best_n, best_s, best_j = validos_primera[0]
            fuente_recomendacion = "primera_linea"
        elif alt:
            best_n, best_s, best_j = alt[0]
            fuente_recomendacion = "alternativa"
        else:
            print("❌ No se encontraron sustitutos ni alternativas válidas.")
            sys.exit(1)
        
        # 9. Obtener efectos secundarios
        efectos_finales = obtener_efectos(best_n, datos['df_info'])
        
        # 10. Mostrar resultados
        print("\n✅ Resultados obtenidos:")
        mostrar_resultado_final(
            composicion_act=composicion_act,
            med_act_es=med_act_es,
            clase_act=clase_act,
            best_n=best_n,
            best_s=best_s,
            best_j=best_j,
            efectos_sust=efectos_finales,
            fuente_recomendacion=fuente_recomendacion,
            df_info=datos['df_info']
        )
        
        # 11. Opción de análisis detallado
        if input("\n¿Ver análisis detallado? (s/n): ").lower().startswith('s'):
            mostrar_analisis_detallado(
                composicion_act=composicion_act,
                med_act_es=med_act_es,
                review_act=review_act,
                clase_act=clase_act,
                comp_principal=comp_principal,
                en_orden=en_orden,
                validos_primera=validos_primera,
                alt=alt,
                best_n=best_n,
                best_s=best_s,
                best_j=best_j,
                efectos_finales=efectos_finales,
                fuente_recomendacion=fuente_recomendacion,
                df_info=datos['df_info']
            )
            
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()