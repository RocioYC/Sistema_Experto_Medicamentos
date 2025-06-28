import pytest
from os.path import dirname, abspath
import pandas as pd

from Vista.rutas import configurar_rutas, cargar_datos
from Modelo.MotorInferencia.Motor_inferencia import (
    obtener_pares_sustitutos,
    score_sustituto,
    obtener_efectos,
    procesar_medicamento_actual,
    buscar_alternativas
)

@pytest.fixture(scope="session")
def datos_reales():
    """
    Carga de una vez todos tus CSV reales usando tu propio loader.
    Devuelve un dict con 'df_info', 'df_sust' y 'lista_alergenos'.
    """
    try:
        base = configurar_rutas()
        datos = cargar_datos(base)
        return datos
    except Exception as e:
        pytest.fail(f"Error cargando datos reales: {e}")

def test_csvs_cargados(datos_reales):
    """Test que verifica que los CSVs se cargaron correctamente"""
    # Asegura que cargaste algo
    assert not datos_reales['df_info'].empty, "df_info está vacío"
    assert not datos_reales['df_sust'].empty, "df_sust está vacío"
    assert isinstance(datos_reales['lista_alergenos'], list), "lista_alergenos no es una lista"
    
    # Verificar columnas esperadas
    assert 'medicamento' in datos_reales['df_info'].columns, "Falta columna 'medicamento' en df_info"
    assert 'medicamento_principal' in datos_reales['df_sust'].columns or 'medicamento' in datos_reales['df_sust'].columns, "Falta columna de medicamento en df_sust"

def test_obtener_pares_sustitutos_real(datos_reales):
    """Test función obtener_pares_sustitutos con datos reales"""
    df_sust = datos_reales['df_sust']
    
    # Identificar la columna correcta de medicamento
    if 'medicamento_principal' in df_sust.columns:
        med_col = 'medicamento_principal'
    elif 'medicamento' in df_sust.columns:
        med_col = 'medicamento'
    else:
        pytest.fail("No se encontró columna de medicamento en df_sust")
    
    # Escogemos un medicamento que seguro existe
    med = df_sust[med_col].iloc[0]
    
    try:
        pares = obtener_pares_sustitutos(med, df_sust)
        
        # Debe ser una lista de tuplas
        assert isinstance(pares, list), "obtener_pares_sustitutos debe devolver una lista"
        assert all(isinstance(p, tuple) and len(p) == 2 for p in pares), "Cada par debe ser una tupla de 2 elementos"
        
        # Si hay pares, verificar estructura
        if pares:
            assert all(isinstance(p[0], str) and isinstance(p[1], str) for p in pares), "Los elementos de las tuplas deben ser strings"
            
    except Exception as e:
        pytest.fail(f"Error en obtener_pares_sustitutos: {e}")

def test_score_sustituto_real(datos_reales):
    """Test función score_sustituto con datos reales"""
    df_info = datos_reales['df_info']
    df_sust = datos_reales['df_sust']
    lista_alergenos = datos_reales['lista_alergenos']
    
    # Identificar columna de medicamento en df_sust
    if 'medicamento_principal' in df_sust.columns:
        med_col = 'medicamento_principal'
    elif 'medicamento' in df_sust.columns:
        med_col = 'medicamento'
    else:
        pytest.skip("No se encontró columna de medicamento en df_sust")
    
    med = df_sust[med_col].iloc[0]
    
    try:
        pares = obtener_pares_sustitutos(med, df_sust)
        if not pares:
            pytest.skip("No hay pares de sustitutos en este CSV de prueba")
        
        en_name = pares[0][1]
        
        # Buscar clase terapéutica
        med_info = df_info[df_info['medicamento'].str.lower() == med.lower()]
        if med_info.empty:
            pytest.skip(f"No se encontró información para {med} en df_info")
        
        # Identificar columna de clase terapéutica
        clase_cols = ['clase_terapeutica', 'clase', 'therapeutic_class']
        clase = None
        for col in clase_cols:
            if col in med_info.columns:
                clase = med_info[col].iloc[0]
                break
        
        if clase is None:
            pytest.skip("No se encontró columna de clase terapéutica")
        
        score, just = score_sustituto(
            es_name=med,
            en_name=en_name,
            notas="El paciente presenta enrojecimiento facial, urticaria y descamacion. refiere alergia previa a tretinoina. diagnosticado con acne . se prescribió tretinoina.",
            diagnostico="acne inflamatorio",
            clase=clase,
            lista_alergenos=lista_alergenos,
            df_info=df_info,
            razon="alergia"
        )
        
        assert isinstance(score, (int, float)), f"Score debe ser numérico, obtuvo {type(score)}"
        assert isinstance(just, str), f"Justificación debe ser string, obtuvo {type(just)}"
        assert just.strip() != "", "La justificación no puede estar vacía"
        
    except Exception as e:
        pytest.fail(f"Error en score_sustituto: {e}")



def test_procesar_medicamento_actual_real(datos_reales):
    """Test función procesar_medicamento_actual con datos reales"""
    df_sust = datos_reales['df_sust']
    df_info = datos_reales['df_info']
    
    # Buscar columna de medicamento en inglés
    en_cols = ['medicamento_en', 'english_name', 'en_name']
    med_en_col = None
    for col in en_cols:
        if col in df_sust.columns:
            med_en_col = col
            break
    
    if med_en_col is None:
        pytest.skip("No se encontró columna de medicamento en inglés en df_sust")
    
    med = df_sust[med_en_col].iloc[0]
    
    try:
        salida = procesar_medicamento_actual(med, df_sust, df_info)
        
        # Debe devolver tupla con al menos 6 elementos
        assert isinstance(salida, tuple), f"Debe devolver tupla, obtuvo {type(salida)}"
        assert len(salida) >= 6, f"Tupla debe tener al menos 6 elementos, tiene {len(salida)}"
        
        # Verificar que el primer elemento no sea None (indica que se encontró)
        assert salida[0] is not None, "No se encontró el medicamento"
        
    except Exception as e:
        pytest.fail(f"Error en procesar_medicamento_actual: {e}")

def test_buscar_alternativas_real(datos_reales):
    """Test función buscar_alternativas con datos reales"""
    df_sust = datos_reales['df_sust']
    df_info = datos_reales['df_info']
    lista_al = datos_reales['lista_alergenos']
    
    # Buscar columna de medicamento en inglés
    en_cols = ['medicamento_en', 'english_name', 'en_name']
    med_en_col = None
    for col in en_cols:
        if col in df_sust.columns:
            med_en_col = col
            break
    
    if med_en_col is None:
        pytest.skip("No se encontró columna de medicamento en inglés")
    
    med = df_sust[med_en_col].iloc[0]
    
    try:
        pares = obtener_pares_sustitutos(med, df_sust)
        respuesta = procesar_medicamento_actual(med, df_sust, df_info)
        
        if respuesta[0] is None:
            pytest.skip("No se pudo procesar el medicamento")
        
        clase_act = respuesta[2]  # la posición 2 es 'clase_act' en tu return
        fila_act = df_info[
            df_info['medicamento'].str.lower() == med.lower()
        ]
        
        if fila_act.empty:
            pytest.skip("No se encontró información del medicamento en df_info")
        
        fila_act = fila_act.iloc[0]
        
        alternativas = buscar_alternativas(
            clase_act,
            "flema",
            fila_act,
            med,
            pares,
            df_info,
            "tos",
            lista_al,
            "desabastecimiento"
        )
        
        assert isinstance(alternativas, list), f"buscar_alternativas debe devolver lista, obtuvo {type(alternativas)}"
        
        # Si hay alternativas, verificar estructura
        if alternativas:
            for alt in alternativas:
                assert isinstance(alt, tuple), "Cada alternativa debe ser una tupla"
                assert len(alt) >= 3, "Cada alternativa debe tener al menos 3 elementos"
                
    except Exception as e:
        pytest.fail(f"Error en buscar_alternativas: {e}")

# Tests adicionales para mayor cobertura
def test_datos_consistency(datos_reales):
    """Test que verifica consistencia entre los datasets"""
    df_info = datos_reales['df_info']
    df_sust = datos_reales['df_sust']
    
    # Verificar que no hay valores nulos en columnas críticas
    assert not df_info['medicamento'].isnull().any(), "Hay valores nulos en medicamento de df_info"
    
    # Verificar tipos de datos
    assert df_info['medicamento'].dtype == 'object', "Columna medicamento debe ser tipo object/string"
    
