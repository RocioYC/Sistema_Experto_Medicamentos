import time
import pytest
import statistics
from unittest.mock import patch
import pandas as pd

from Vista.interfaz_principal import SistemaMedicamentosGUI
from Vista.rutas import configurar_rutas, cargar_datos


@pytest.fixture(scope="module")
def datos_rendimiento():
    """Fixture que carga datos una sola vez para todos los tests de rendimiento"""
    try:
        return cargar_datos(configurar_rutas())
    except Exception as e:
        pytest.skip(f"No se pudieron cargar datos para test de rendimiento: {e}")

@pytest.fixture(scope="module") 
def gui_rendimiento():
    """GUI instance para tests de rendimiento"""
    try:
        return SistemaMedicamentosGUI()
    except Exception as e:
        pytest.skip(f"No se pudo crear GUI para test de rendimiento: {e}")

@pytest.mark.performance
def test_inferencia_rapida(datos_rendimiento, gui_rendimiento):
    """Test que verifica que la inferencia se ejecuta en tiempo razonable"""
    
    # Parámetros de prueba
    notas = "Paciente presenta fiebre y malestar general"
    diagnostico = "infección"
    med = "amoxicilina"  # Medicamento común
    razon = "alergia"
    
    # Medición de tiempo
    tiempos = []
    num_iteraciones = 3  # Múltiples mediciones para obtener promedio
    
    for i in range(num_iteraciones):
        t0 = time.perf_counter()
        
        try:
            resultado = gui_rendimiento.procesar_medicamento(
                med, notas, diagnostico, datos_rendimiento, razon
            )
            
            elapsed = time.perf_counter() - t0
            tiempos.append(elapsed)
            
            # Verificar que no hay error
            assert not (isinstance(resultado, dict) and resultado.get("status") == "error"), \
                   f"Error en iteración {i+1}: {resultado}"
                   
        except Exception as e:
            pytest.fail(f"Error en iteración {i+1}: {e}")
    
    # Análisis de rendimiento
    tiempo_promedio = statistics.mean(tiempos)
    tiempo_maximo = max(tiempos)
    tiempo_minimo = min(tiempos)
    
    # Aserciones de rendimiento
    assert tiempo_promedio < 2.0, f"Inferencia promedio demasiado lenta: {tiempo_promedio:.3f}s"
    assert tiempo_maximo < 3.0, f"Inferencia más lenta excede límite: {tiempo_maximo:.3f}s"
    
    print(f"\nEstadísticas de rendimiento:")
    print(f"Tiempo promedio: {tiempo_promedio:.3f}s")
    print(f"Tiempo mínimo: {tiempo_minimo:.3f}s") 
    print(f"Tiempo máximo: {tiempo_maximo:.3f}s")

@pytest.mark.performance
def test_carga_datos_rapida():
    """Test que verifica que la carga de datos es eficiente"""
    
    t0 = time.perf_counter()
    
    try:
        datos = cargar_datos(configurar_rutas())
        elapsed = time.perf_counter() - t0
        
        # La carga de datos debe ser rápida
        assert elapsed < 5.0, f"Carga de datos demasiado lenta: {elapsed:.3f}s"
        
        # Verificar que se cargaron datos válidos
        assert not datos['df_info'].empty, "df_info está vacío"
        assert not datos['df_sust'].empty, "df_sust está vacío"
        assert isinstance(datos['lista_alergenos'], list), "lista_alergenos no es lista"
        
        print(f"\nTiempo de carga de datos: {elapsed:.3f}s")
        
    except Exception as e:
        pytest.fail(f"Error cargando datos: {e}")

