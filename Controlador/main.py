import sys
import pandas as pd
import time
from os.path import dirname, abspath

# Configuración de rutas
project_dir = dirname(dirname(abspath(__file__)))
sys.path.append(project_dir)

# Importaciones optimizadas
from Vista.rutas import configurar_rutas, cargar_datos
from Modelo.MotorInferencia.Motor_inferencia import (
    obtener_pares_sustitutos, 
    score_sustituto, 
    obtener_efectos,
    procesar_medicamento_actual,
    buscar_alternativas
)
from Vista.presentacion_explicativa_main import (
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
    """Solicita y valida los datos del paciente, incluyendo la razón para sustitución"""
    print("\n" + "="*50)
    print(" INGRESO DE DATOS DEL PACIENTE ".center(50, "="))
    print("="*50)

    # 0. Razón para sustitución (nuevo)
    print("\n🔍 MOTIVO DE SUSTITUCIÓN:")
    print("1. Alergia o reacción adversa")
    print("2. Desabastecimiento/falta de stock")
    while True:
        razon = input("└─ Seleccione el motivo (1/2): ").strip()
        if razon in ['1', '2']:
            razon = 'alergia' if razon == '1' else 'desabastecimiento'
            break
        print("❌ Opción inválida. Intente nuevamente.")

    # 1. Notas clínicas (reutiliza alergias si es por alergia)
    print("\n📝 NOTAS CLÍNICAS:")
    sintomas = validar_entrada("└─ Síntomas principales: ", "texto")
    historia = validar_entrada("└─ Antecedentes relevantes: ", "texto")
    while True:
        raw = input("└─ ¿A qué medicamento es alérgico? (o Enter si ninguno): ")
        # Si el usuario sólo pulsa ENTER, raw == ""
        if raw == "":
            alergias = "ninguna"
            break
        # Si escribió algo, al menos 3 caracteres
        if len(raw.strip()) < 3:
            print("❌ Por favor escribe al menos 3 caracteres o pulsa Enter para 'ninguna'")
            continue
        alergias = raw.strip()
        break

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
    print(f"🔹 Síntomas: {sintomas[:180]}...")
    print(f"🔹 Diagnóstico: {diagnostico}")
    print(f"🔹 Medicamento: {med_input}")
    
    while True:
        confirm = input("\n¿Los datos son correctos? (s/n): ").strip().lower()
        if confirm == 's':
            break
        elif confirm == 'n':
            print("\n¿Qué deseas editar?")
            print("1. Síntomas")
            print("2. Antecedentes")
            print("3. Alergias")
            print("4. Diagnóstico")
            print("5. Medicamento")
            print("6. Todo")
            opcion = input("Seleccione una opción (1-6): ").strip()

            if opcion == '1':
                sintomas = validar_entrada("└─ Síntomas principales: ", "texto")
            elif opcion == '2':
                historia = validar_entrada("└─ Antecedentes relevantes: ", "texto")
            elif opcion == '3':
                while True:
                    raw = input("└─ ¿A qué medicamento es alérgico? (o Enter si ninguno): ")
                    if raw.strip() == "":
                        alergias = "ninguna"
                        break
                    if len(raw.strip()) < 3:
                        print("❌ Por favor escribe al menos 3 caracteres o pulsa Enter para 'ninguna'")
                        continue
                    alergias = raw.strip()
                    break
            elif opcion == '4':
                diagnostico = validar_entrada("└─ Diagnóstico principal: ", "diagnostico")
            elif opcion == '5':
                med_input = validar_entrada("└─ Nombre comercial o principio activo: ", "medicamento")
            elif opcion == '6':
                print("\nReingresando todos los datos...\n")
                return solicitar_datos_paciente()
            else:
                print("❌ Opción inválida. Intenta nuevamente.")

            # Volver a mostrar resumen actualizado
            notas = f"Síntomas: {sintomas}\nHistoria: {historia}\nAlergias: {alergias}"
            print("\n" + "-"*50)
            print(" RESUMEN DE DATOS ".center(50, "-"))
            print(f"🔹 Síntomas: {sintomas[:180]}...")
            print(f"🔹 Diagnóstico: {diagnostico}")
            print(f"🔹 Medicamento: {med_input}")
        else:
            print("❌ Entrada inválida. Escribe 's' o 'n'")
    
    return notas, diagnostico, med_input, razon 

def procesar_medicamento(med_input, notas, diagnostico, datos, razon=None):
    """
    Procesa el medicamento considerando la razón (alergia/desabastecimiento)
    
    Parámetros:
        med_input: nombre del medicamento ingresado
        notas: notas clínicas del paciente
        diagnostico: diagnóstico principal
        datos: diccionario con dataframes y listas necesarias
        razon: motivo de la sustitución ('alergia' o 'desabastecimiento')
    """
    # Limpieza previa de datos manteniendo tipos numéricos (opcional pero recomendado)
    if 'df_info' in datos and hasattr(datos['df_info'], 'copy'):
        datos['df_info'] = limpiar_dataframe(datos['df_info'])
    if 'df_sust' in datos and hasattr(datos['df_sust'], 'copy'):
        datos['df_sust'] = limpiar_dataframe(datos['df_sust'])
    
    # Obtener información del medicamento actual
    resultados = procesar_medicamento_actual(med_input, datos['df_sust'], datos['df_info'])
    
    # Si no se encontró el medicamento, retornar None o un mensaje de error según tu implementación original
    if not resultados[0]:
        return {
            "status": "error",
            "message": "No se encontró información del medicamento ingresado"
        }
    
    med_act_en, med_act_es, clase_act, review_act, composicion_act, comp_principal = resultados
    
    # Obtener los pares de sustitutos
    sust_pairs = obtener_pares_sustitutos(med_act_en, datos['df_sust'])
    en_orden = []
    
    # Evaluar cada sustituto considerando la razón (CAMBIO IMPORTANTE)
    for es_name, en_name in sust_pairs:
        score, just = score_sustituto(
            es_name, en_name, notas, 
            diagnostico, clase_act, 
            datos['lista_alergenos'], datos['df_info'],
            razon  # Pasar la razón al evaluador
        )
        en_orden.append((en_name, score, just))
    
    # Ordenar sustitutos por score y limitar a los 5 mejores
    en_orden = sorted(en_orden, key=lambda x: x[1], reverse=True)[:5]
    
    # Filtrar válidos según tu implementación original
    validos = [c for c in en_orden 
                if "❌ Alergia detectada" not in c[2] 
                and "⚠️ Información no encontrada" not in c[2]]
    
    # Buscar alternativas adicionales (también pasando la razón)
    alternativas = []
    if not validos:
        fila_act = datos['df_info'][datos['df_info']["medicamento"].str.lower() == med_act_en.lower()].iloc[0]
        alternativas = buscar_alternativas(
        clase_act, diagnostico, fila_act, 
        med_act_en, sust_pairs, datos['df_info'], 
        notas, datos['lista_alergenos'],
        razon
    )
    
    response = {
        'medicamento': med_act_es,
        'composicion': composicion_act,
        'clase': clase_act,
        'componente': comp_principal,
        'sustitutos': en_orden,
        'validos': validos,
        'alternativas': alternativas,
        'review': review_act,
        'razon_sustitucion': razon  # Añadir la razón en la respuesta puede ser útil
    }
    
    return response

# Función auxiliar para limpiar datos (según la implementación del profesor)
def limpiar_dataframe(df):
    """Limpia un dataframe manteniendo los tipos numéricos donde sea posible"""
    df_copy = df.copy()
    for col in df_copy.columns:
        if df_copy[col].dtype == object:  # Solo para columnas de texto
            df_copy[col] = df_copy[col].apply(lambda x: limpiar_y_convertir(x))
    return df_copy

def limpiar_y_convertir(valor):
    """Convierte valores a string y limpia NaN/None, manteniendo números como números"""
    if pd.isna(valor):
        return ""
    try:
        # Intentar mantener como número si es posible
        return float(valor) if str(valor).replace('.', '', 1).isdigit() else str(valor).strip()
    except:
        return str(valor).strip()

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

        tiempos = []   # <--- aquí guardaremos cada tiempo de respuesta
        
        while True:
            # Solicitar datos
            notas, diagnostico, med_input, razon = solicitar_datos_paciente() 

            t0 = time.perf_counter()
            
            # Procesar medicamento
            resultado = procesar_medicamento(med_input, notas, diagnostico, datos, razon)
            
            if isinstance(resultado, dict) and resultado.get('status') == 'error':
                print(f"\n❌ {resultado['message']}")
                opcion = mostrar_opciones_reintento()
                if opcion == '1':
                    continue  # reintentar con otro medicamento
                elif opcion == '2':
                    continue  # volver a ingresar todos los datos
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
                df_info=datos['df_info'],
                df_sust=datos['df_sust']
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
                    df_info=datos['df_info'],
                    df_sust=datos['df_sust']
                )
            
            ##################TIEMPO##########################

            t1 = time.perf_counter()
            elapsed = t1 - t0
            tiempos.append(elapsed)
            print(f"\n  ⌛ Tiempo de respuesta: {elapsed:.3f} s")

            
            if len(tiempos) >= 3:
                avg = sum(tiempos) / len(tiempos)
                print(f"🔢 Tiempo promedio sobre {len(tiempos)} casos: {avg:.3f} s\n")
                tiempos.clear()   # empieza a contar de nuevo si quieres repetir
            ##################TIEMPO##########################

            # Opción de nuevo análisis
            if input("\n¿Desea realizar otra consulta? (s/n): ").lower() != 's':
                print("\n👋 Programa terminado.")
                break
                
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()