import sys
import pandas as pd
from os.path import dirname, abspath

# Configuración de rutas
project_dir = dirname(dirname(abspath(__file__)))
sys.path.append(project_dir)

# Importaciones optimizadas
from Vista.rutas import configurar_rutas, cargar_datos
from Modelo.MotorInferencia.Motor_inferencia_Data import (
    obtener_pares_sustitutos, 
    score_sustituto, 
    obtener_efectos,
    procesar_medicamento_actual,
    buscar_alternativas
)
from Vista.presentacion_explicativa import (
    mostrar_resultado_final, 
    mostrar_analisis_detallado
)

def limpiar_y_convertir(valor):
    """Convierte valores a string y limpia NaN/None, manteniendo números como números"""
    if pd.isna(valor):
        return ""
    try:
        # Intentar mantener como número si es posible
        return float(valor) if str(valor).replace('.', '', 1).isdigit() else str(valor).strip()
    except:
        return str(valor).strip()

def limpiar_dataframe(df):
    """Limpia un dataframe manteniendo los tipos numéricos donde sea posible"""
    for col in df.columns:
        if df[col].dtype == object:  # Solo para columnas de texto
            df[col] = df[col].apply(lambda x: limpiar_y_convertir(x))
    return df

def validar_entrada(prompt, tipo="texto", min_len=3):
    """
    Valida la entrada del usuario con diferentes criterios según el tipo
    Tipos disponibles: 'texto', 'medicamento', 'diagnostico'
    """
    while True:
        entrada = input(prompt).strip()
        
        if not entrada:
            print("❌ Este campo no puede estar vacío")
            continue
            
        if tipo == "medicamento" and len(entrada) < min_len:
            print(f"❌ El medicamento debe tener al menos {min_len} caracteres")
            continue
            
        if tipo == "diagnostico" and len(entrada) < min_len:
            print(f"❌ El diagnóstico debe tener al menos {min_len} caracteres")
            continue
            
        return entrada


def solicitar_datos_paciente():
    """Solicita y valida los datos del paciente con interfaz mejorada"""
    print("\n" + "="*50)
    print(" INGRESO DE DATOS DEL PACIENTE ".center(50, "="))
    print("="*50)
    
    # 1. Notas clínicas
    print("\n📝 NOTAS CLÍNICAS:")
    sintomas = validar_entrada("└─ Síntomas principales: ", "texto")
    historia = validar_entrada("└─ Antecedentes relevantes: ", "texto")
    alergias = validar_entrada("└─ Alergias conocidas (o 'ninguna'): ", "texto")
    notas = f"Síntomas: {sintomas}\nHistoria: {historia}\nAlergias: {alergias}"
    
    # 2. Diagnóstico
    print("\n🩺 DIAGNÓSTICO (1 palabra):")
    diagnostico = validar_entrada("└─ Diagnóstico principal: ", "diagnostico")
    
    # 3. Medicamento
    print("\n💊 MEDICAMENTO ACTUAL:")
    med_input = validar_entrada("└─ Nombre comercial o principio activo: ", "medicamento")
    
    # Confirmación
    print("\n" + "-"*50)
    print(" RESUMEN DE DATOS ".center(50, "-"))
    print(f"🔹 Síntomas: {sintomas[:100]}...")
    print(f"🔹 Diagnóstico: {diagnostico}")
    print(f"🔹 Medicamento: {med_input}")
    
    if input("\n¿Los datos son correctos? (s/n): ").lower() != 's':
        print("\nReingresando datos...\n")
        return solicitar_datos_paciente()
    
    return notas, diagnostico, med_input

def procesar_medicamento(med_input, notas, diagnostico, datos):
    """Procesa un medicamento y devuelve resultados o None si no se encuentra"""
    # Limpieza previa de datos manteniendo tipos numéricos
    datos['df_info'] = limpiar_dataframe(datos['df_info'])
    datos['df_sust'] = limpiar_dataframe(datos['df_sust'])
    
    resultados = procesar_medicamento_actual(med_input, datos['df_sust'], datos['df_info'])
    if not resultados[0]:  # Si no se encontró el medicamento
        return None
    
    med_act_en, med_act_es, clase_act, review_act, composicion_act, comp_principal = resultados
    
    # Obtener sustitutos
    sust_pairs = obtener_pares_sustitutos(med_act_en, datos['df_sust'])
    en_orden = []
    
    for es_name, en_name in sust_pairs:
        score, just = score_sustituto(
            es_name, en_name, notas, 
            diagnostico, clase_act, 
            datos['lista_alergenos'], datos['df_info']
        )
        en_orden.append((en_name, score, just))
    
    en_orden.sort(key=lambda x: x[1], reverse=True)
    
    # Filtrar válidos
    validos = [c for c in en_orden 
              if "❌ Alergia detectada" not in c[2] 
              and "⚠️ Información no encontrada" not in c[2]]
    
    # Buscar alternativas si no hay sustitutos válidos
    alternativas = []
    if not validos:
        fila_act = datos['df_info'][datos['df_info']["medicamento"].str.lower() == med_act_en.lower()].iloc[0]
        alternativas = buscar_alternativas(
            clase_act, diagnostico, fila_act, 
            med_act_en, sust_pairs, datos['df_info'], 
            notas, datos['lista_alergenos']
        )
    
    return {
        'medicamento': med_act_es,
        'composicion': composicion_act,
        'clase': clase_act,
        'componente': comp_principal,
        'sustitutos': en_orden,
        'validos': validos,
        'alternativas': alternativas,
        'review': review_act
    }

def mostrar_opciones_reintento():
    """Muestra opciones cuando falla el procesamiento"""
    print("\n" + "="*50)
    print(" OPCIONES ".center(50, "="))
    print("1. Ingresar otro medicamento")
    print("2. Volver a ingresar todos los datos")
    print("3. Salir del programa")
    
    while True:
        opcion = input("Seleccione una opción (1-3): ").strip()
        if opcion in ['1', '2', '3']:
            return opcion
        print("❌ Opción inválida. Intente nuevamente.")

def main():
    try:
        # Configuración inicial
        print("\n" + "="*50)
        print(" SISTEMA EXPERTO DE SUSTITUCIÓN DE MEDICAMENTOS ".center(50, "="))
        print("="*50)
        
        # Cargar y limpiar datos
        datos = cargar_datos(configurar_rutas())
        datos['lista_alergenos'] = [limpiar_y_convertir(a) for a in datos['lista_alergenos']]
        
        while True:
            # Solicitar datos
            notas, diagnostico, med_input = solicitar_datos_paciente()
            
            # Procesar medicamento
            resultado = procesar_medicamento(med_input, notas, diagnostico, datos)
            
            if not resultado:
                print(f"\n❌ No se encontró el medicamento '{med_input}'")
                opcion = mostrar_opciones_reintento()
                
                if opcion == '1':
                    continue
                elif opcion == '2':
                    continue  # Volverá al inicio del while
                else:
                    print("\n👋 Programa terminado.")
                    sys.exit()
            
            # Determinar mejor recomendación
            if resultado['validos']:
                recomendacion = resultado['validos'][0]
                fuente = "sustituto_directo"
            elif resultado['alternativas']:
                recomendacion = resultado['alternativas'][0]
                fuente = "alternativa_terapeutica"
            else:
                print("\n❌ No se encontraron opciones válidas")
                opcion = mostrar_opciones_reintento()
                
                if opcion == '1':
                    continue
                elif opcion == '2':
                    continue
                else:
                    print("\n👋 Programa terminado.")
                    sys.exit()
            
            # Mostrar resultados
            efectos = obtener_efectos(recomendacion[0], datos['df_info'])
            
            mostrar_resultado_final(
                composicion_act=resultado['composicion'],
                med_act_es=resultado['medicamento'],
                clase_act=resultado['clase'],
                best_n=recomendacion[0],
                best_s=recomendacion[1],
                best_j=recomendacion[2],
                efectos_sust=efectos,
                fuente_recomendacion=fuente,
                df_info=datos['df_info']
            )
            
            # Opción de análisis detallado
            if input("\n¿Ver análisis detallado? (s/n): ").lower() == 's':
                mostrar_analisis_detallado(
                    composicion_act=resultado['composicion'],
                    med_act_es=resultado['medicamento'],
                    review_act=resultado['review'],
                    clase_act=resultado['clase'],
                    comp_principal=resultado['componente'],
                    en_orden=resultado['sustitutos'],
                    validos_primera=resultado['validos'],
                    alt=resultado['alternativas'],
                    best_n=recomendacion[0],
                    best_s=recomendacion[1],
                    best_j=recomendacion[2],
                    efectos_finales=efectos,
                    fuente_recomendacion=fuente,
                    df_info=datos['df_info']
                )
            
            # Opción de nuevo análisis
            if input("\n¿Desea realizar otra consulta? (s/n): ").lower() != 's':
                print("\n👋 Programa terminado.")
                break
                
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()