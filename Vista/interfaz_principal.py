import sys
import pandas as pd
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from threading import Thread
from os.path import dirname, abspath

# Configuración de rutas 
project_dir = dirname(dirname(abspath(__file__)))
sys.path.append(project_dir)

from Vista.rutas import configurar_rutas, cargar_datos
from Modelo.MotorInferencia.Motor_inferencia import (
    obtener_pares_sustitutos, 
    score_sustituto, 
    obtener_efectos,
    procesar_medicamento_actual,
    buscar_alternativas
)


class SistemaMedicamentosGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema Experto - Sustitución de Medicamentos")
        self.root.geometry("830x800")
        self.root.configure(bg='#f0f0f0')
        
        # Variables de datos
        self.datos = None
        self.resultado_actual = None
        self.tiempos = []
        
        # Configurar estilos
        self.configurar_estilos()
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Cargar datos al iniciar
        self.cargar_datos_inicial()
    
    def configurar_estilos(self):
        """Configura los estilos de la aplicación"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Estilo para botones principales
        style.configure('Main.TButton', 
                       font=('Arial', 10, 'bold'), 
                       padding=10)
        
        # Estilo para frames principales
        style.configure('Main.TFrame', 
                       background='#f0f0f0')
        
        # Estilo para labels de título
        style.configure('Title.TLabel', 
                       font=('Arial', 14, 'bold'), 
                       background='#f0f0f0')
        
        # Estilo para labels de sección
        style.configure('Section.TLabel', 
                       font=('Arial', 12, 'bold'), 
                       background='#f0f0f0')
    
    def crear_interfaz(self):
        """Crea la interfaz principal"""
        # Frame principal
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = ttk.Label(main_frame, 
                               text="Sistema Experto de Sustitución de Medicamentos", 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Crear notebook para pestañas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de ingreso de datos
        self.crear_pestaña_ingreso()
        
        # Pestaña de resultados
        self.crear_pestaña_resultados()
        
        # Frame de botones principales
        self.crear_botones_principales(main_frame)
        
        # Barra de estado
        self.crear_barra_estado(main_frame)
    
    def crear_pestaña_ingreso(self):
        """Crea la pestaña de ingreso de datos del paciente"""
        # Frame de ingreso
        self.frame_ingreso = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_ingreso, text="Datos del Paciente")
        
        # Crear scrollable frame
        canvas = tk.Canvas(self.frame_ingreso, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(self.frame_ingreso, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 1. Motivo de sustitución
        motivo_frame = ttk.LabelFrame(scrollable_frame, text="🔍 Motivo de Sustitución", padding=15)
        motivo_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.var_motivo = tk.StringVar(value="alergia")
        ttk.Radiobutton(motivo_frame, text="Alergia o reacción adversa", 
                       variable=self.var_motivo, value="alergia").pack(anchor=tk.W)
        ttk.Radiobutton(motivo_frame, text="Desabastecimiento/falta de stock", 
                       variable=self.var_motivo, value="desabastecimiento").pack(anchor=tk.W)
        
        # 2. Notas clínicas
        notas_frame = ttk.LabelFrame(scrollable_frame, text="📝 Notas Clínicas", padding=15)
        notas_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Síntomas
        ttk.Label(notas_frame, text="Síntomas principales:").pack(anchor=tk.W)
        self.entry_sintomas = tk.Text(notas_frame, height=3, width=80, wrap=tk.WORD)
        self.entry_sintomas.pack(fill=tk.X, pady=(5, 10))
        
        # Antecedentes
        ttk.Label(notas_frame, text="Antecedentes relevantes:").pack(anchor=tk.W)
        self.entry_historia = tk.Text(notas_frame, height=3, width=80, wrap=tk.WORD)
        self.entry_historia.pack(fill=tk.X, pady=(5, 10))
        
        # Alergias
        ttk.Label(notas_frame, text="¿A qué medicamento es alérgico? (opcional):").pack(anchor=tk.W)
        self.entry_alergias = ttk.Entry(notas_frame, width=80)
        self.entry_alergias.pack(fill=tk.X, pady=(5, 0))
        self.entry_alergias.insert(0, "ninguna")
        
        # 3. Diagnóstico
        diagnostico_frame = ttk.LabelFrame(scrollable_frame, text="🩺 Diagnóstico", padding=15)
        diagnostico_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(diagnostico_frame, text="Diagnóstico principal (1 palabra):").pack(anchor=tk.W)
        self.entry_diagnostico = ttk.Entry(diagnostico_frame, width=80, font=('Arial', 11))
        self.entry_diagnostico.pack(fill=tk.X, pady=(5, 0))
        
        # 4. Medicamento
        medicamento_frame = ttk.LabelFrame(scrollable_frame, text="💊 Medicamento Actual", padding=15)
        medicamento_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(medicamento_frame, text="Nombre comercial o principio activo:").pack(anchor=tk.W)
        self.entry_medicamento = ttk.Entry(medicamento_frame, width=80, font=('Arial', 12, 'bold'))
        self.entry_medicamento.pack(fill=tk.X, pady=(5, 0))
        
        # Botón de validación
        ttk.Button(medicamento_frame, text="Validar Datos", 
                  command=self.validar_datos, style='Main.TButton').pack(pady=10)
        
    def crear_pestaña_resultados(self):
        """Crea la pestaña de resultados"""
        self.frame_resultados = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_resultados, text="Resultados")
        
        # Crear scrollable frame para resultados
        canvas_res = tk.Canvas(self.frame_resultados, bg='#f0f0f0')
        scrollbar_res = ttk.Scrollbar(self.frame_resultados, orient="vertical", command=canvas_res.yview)
        self.scrollable_resultados = ttk.Frame(canvas_res)
        
        self.scrollable_resultados.bind(
            "<Configure>",
            lambda e: canvas_res.configure(scrollregion=canvas_res.bbox("all"))
        )
        
        canvas_res.create_window((0, 0), window=self.scrollable_resultados, anchor="nw")
        canvas_res.configure(yscrollcommand=scrollbar_res.set)
        
        canvas_res.pack(side="left", fill="both", expand=True)
        scrollbar_res.pack(side="right", fill="y")
        
        # Label inicial
        self.label_resultados = ttk.Label(self.scrollable_resultados, 
                                         text="Los resultados aparecerán aquí después del análisis...",
                                         font=('Arial', 12))
        self.label_resultados.pack(pady=50)
    
    def crear_botones_principales(self, parent):
        """Crea los botones principales de acción"""
        botones_frame = ttk.Frame(parent)
        botones_frame.pack(fill=tk.X, pady=10)
        
        # Botón de procesar
        self.btn_procesar = ttk.Button(botones_frame, text="🔍 Procesar Medicamento", 
                                      command=self.procesar_medicamento_thread,
                                      style='Main.TButton', state='disabled')
        self.btn_procesar.pack(side=tk.LEFT, padx=5)
        
        # Botón de análisis detallado
        self.btn_detallado = ttk.Button(botones_frame, text="📊 Análisis Detallado", 
                                       command=self.mostrar_analisis_detallado,
                                       style='Main.TButton', state='disabled')
        self.btn_detallado.pack(side=tk.LEFT, padx=5)
        
        # Botón de nueva consulta
        ttk.Button(botones_frame, text="🔄 Nueva Consulta", 
                  command=self.nueva_consulta,
                  style='Main.TButton').pack(side=tk.LEFT, padx=5)
        
        # Botón de salir
        ttk.Button(botones_frame, text="❌ Salir", 
                  command=self.salir,
                  style='Main.TButton').pack(side=tk.RIGHT, padx=5)
    
    def crear_barra_estado(self, parent):
        """Crea la barra de estado"""
        self.status_frame = ttk.Frame(parent)
        self.status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(self.status_frame, text="Listo para procesar...")
        self.status_label.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=(10, 0))
    
    def cargar_datos_inicial(self):
        """Carga los datos iniciales del sistema"""
        try:
            self.status_label.config(text="Cargando datos del sistema...")
            self.progress.start()
            
            # Cargar datos
            self.datos = cargar_datos(configurar_rutas())
            self.datos['lista_alergenos'] = [self.limpiar_y_convertir(a) for a in self.datos['lista_alergenos']]
            
            self.progress.stop()
            self.status_label.config(text="Sistema listo - Datos cargados correctamente")
            
        except Exception as e:
            self.progress.stop()
            self.status_label.config(text="Error al cargar datos")
            messagebox.showerror("Error", f"Error al cargar datos del sistema:\n{str(e)}")
    
    def validar_datos(self):
        """Valida los datos ingresados"""
        errores = []
        
        # Validar campos obligatorios
        if not self.entry_sintomas.get("1.0", tk.END).strip():
            errores.append("• Los síntomas son obligatorios")
        
        if not self.entry_historia.get("1.0", tk.END).strip():
            errores.append("• Los antecedentes son obligatorios")
            
        if not self.entry_diagnostico.get().strip():
            errores.append("• El diagnóstico es obligatorio")
            
        if not self.entry_medicamento.get().strip():
            errores.append("• El medicamento es obligatorio")
        
        # Validar longitud mínima
        if len(self.entry_diagnostico.get().strip()) < 3:
            errores.append("• El diagnóstico debe tener al menos 3 caracteres")
            
        if len(self.entry_medicamento.get().strip()) < 3:
            errores.append("• El medicamento debe tener al menos 3 caracteres")
        
        if errores:
            messagebox.showerror("Errores de validación", "\n".join(errores))
            return False
        
        # Si todo está bien
        messagebox.showinfo("Validación", "✅ Todos los datos son válidos\nYa puede procesar el medicamento")
        self.btn_procesar.config(state='normal')
        return True
    
    def procesar_medicamento_thread(self):
        """Ejecuta el procesamiento en un hilo separado"""
        # Deshabilitar botón durante procesamiento
        self.btn_procesar.config(state='disabled')
        self.progress.start()
        self.status_label.config(text="Procesando medicamento...")
        
        # Ejecutar en hilo separado
        thread = Thread(target=self.procesar_medicamento_logica)
        thread.daemon = True
        thread.start()
    
    def procesar_medicamento_logica(self):
        """Lógica principal de procesamiento"""
        try:
            t0 = time.perf_counter()
            
            # Obtener datos del formulario
            sintomas = self.entry_sintomas.get("1.0", tk.END).strip()
            historia = self.entry_historia.get("1.0", tk.END).strip()
            alergias = self.entry_alergias.get().strip() or "ninguna"
            diagnostico = self.entry_diagnostico.get().strip()
            medicamento = self.entry_medicamento.get().strip()
            razon = self.var_motivo.get()
            
            notas = f"Síntomas: {sintomas}\nHistoria: {historia}\nAlergias: {alergias}"
            
            # Procesar medicamento (usando tu función original)
            resultado = self.procesar_medicamento(medicamento, notas, diagnostico, self.datos, razon)
            
            t1 = time.perf_counter()
            elapsed = t1 - t0
            self.tiempos.append(elapsed)
            
            # Actualizar interfaz en el hilo principal
            self.root.after(0, self.mostrar_resultados, resultado, elapsed)
            
        except Exception as e:
            self.root.after(0, self.mostrar_error, str(e))
    
    def mostrar_resultados(self, resultado, tiempo_procesamiento):
        """Muestra los resultados en la interfaz"""
        self.progress.stop()
        self.btn_procesar.config(state='normal')
        
        if isinstance(resultado, dict) and resultado.get('status') == 'error':
            self.status_label.config(text="Error en el procesamiento")
            messagebox.showerror("Error", resultado['message'])
            return
        
        self.resultado_actual = resultado
        
        # Limpiar frame de resultados
        for widget in self.scrollable_resultados.winfo_children():
            widget.destroy()
        
        # Determinar mejor recomendación
        if resultado['validos']:
            recomendacion = resultado['validos'][0]
            fuente = "sustituto_directo"
        elif resultado['alternativas']:
            recomendacion = resultado['alternativas'][0]
            fuente = "alternativa_terapeutica"
        else:
            self.mostrar_sin_opciones()
            return
        
        # Obtener efectos
        efectos = obtener_efectos(recomendacion[0], self.datos['df_info'])
        
        # Mostrar información del medicamento actual
        self.mostrar_medicamento_actual(resultado)
        
        # Mostrar recomendación principal
        self.mostrar_recomendacion_principal(recomendacion, efectos, fuente)
        
        # Mostrar otras opciones
        self.mostrar_otras_opciones(resultado)
        
        # Mostrar tiempo y estadísticas
        self.mostrar_estadisticas(tiempo_procesamiento)
        
        # Cambiar a pestaña de resultados
        self.notebook.select(1)
        self.btn_detallado.config(state='normal')
        
        self.status_label.config(text=f"Procesamiento completado en {tiempo_procesamiento:.3f}s")
    
    def mostrar_medicamento_actual(self, resultado):
        """Muestra información del medicamento actual"""
        frame_actual = ttk.LabelFrame(self.scrollable_resultados, 
                                     text="💊 Medicamento Actual", padding=15)
        frame_actual.pack(fill=tk.X, padx=10, pady=10)
        
        info_text = f"""
Medicamento: {resultado['medicamento']}
Composición: {resultado['composicion']}
Clase Terapéutica: {resultado['clase']}
Componente Principal: {resultado['componente']}
        """.strip()
        
        ttk.Label(frame_actual, text=info_text, font=('Arial', 10)).pack(anchor=tk.W)
    
    def mostrar_recomendacion_principal(self, recomendacion, efectos, fuente):
        """Muestra la recomendación principal"""
        frame_rec = ttk.LabelFrame(self.scrollable_resultados, 
                                  text="✅ Recomendación Principal", padding=15)
        frame_rec.pack(fill=tk.X, padx=10, pady=10)
        
        # Título con score
        titulo = f"🏆 (Score: {recomendacion[1]:.1f})"
        ttk.Label(frame_rec, text=titulo, font=('Arial', 14, 'bold'), 
                 foreground='green').pack(anchor=tk.W, pady=(0, 10))
        
        # Obtener composición del medicamento recomendado
        try:
            fila_recomendado = self.datos['df_info'][
                self.datos['df_info']["medicamento"].str.lower() == recomendacion[0].lower()
            ].iloc[0]
            composicion_recomendado = fila_recomendado.get('composicion', 'No disponible')
        except:
            composicion_recomendado = 'No disponible'
        
        # Información esencial (COMPOSICIÓN DESTACADA)
        info_frame = ttk.Frame(frame_rec)
        info_frame.pack(fill=tk.X, pady=5)
        
        # Composición en destacado
        composicion_frame = ttk.LabelFrame(info_frame, text="🧪 COMPOSICIÓN", padding=10)
        composicion_frame.pack(fill=tk.X, pady=(0, 10))
        composicion_label = ttk.Label(composicion_frame, text=composicion_recomendado, 
                                     font=('Arial', 12, 'bold'), foreground='blue',
                                     wraplength=800)
        composicion_label.pack(anchor=tk.W)
        
        # Justificación
        justif_text = scrolledtext.ScrolledText(frame_rec, height=4, width=80, wrap=tk.WORD)
        justif_text.pack(fill=tk.X, pady=(10, 0))
        justif_text.insert(tk.END, f"Justificación:\n {recomendacion[2]}")
        justif_text.config(state=tk.DISABLED)
        
        # Efectos secundarios
        if efectos:
            ttk.Label(frame_rec, text="⚠️ Efectos Secundarios:", 
                     font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
            efectos_text = scrolledtext.ScrolledText(frame_rec, height=3, width=80, wrap=tk.WORD)
            efectos_text.pack(fill=tk.X)
            efectos_text.insert(tk.END, efectos)
            efectos_text.config(state=tk.DISABLED)
        
        # Fuente de recomendación
        fuente_texto = "Recomendación directa" if fuente == "sustituto_directo" else "Alternativa terapéutica"
        ttk.Label(frame_rec, text=f"📋 Tipo: {fuente_texto}", 
                 font=('Arial', 9), foreground='gray').pack(anchor=tk.W, pady=(10, 0))
    
    def mostrar_otras_opciones(self, resultado):
        """Muestra otras opciones disponibles"""
        if len(resultado['validos']) > 1 or resultado['alternativas']:
            frame_otras = ttk.LabelFrame(self.scrollable_resultados, 
                                        text="📋 Otras Opciones", padding=15)
            frame_otras.pack(fill=tk.X, padx=10, pady=10)
            
            # Crear treeview para mostrar opciones
            columns = ('Medicamento', 'Score', 'Tipo')
            tree = ttk.Treeview(frame_otras, columns=columns, show='headings', height=6)
            
            tree.heading('Medicamento', text='Medicamento')
            tree.heading('Score', text='Score')
            tree.heading('Tipo', text='Tipo')
            
            tree.column('Medicamento', width=300)
            tree.column('Score', width=80)
            tree.column('Tipo', width=150)
            
            # Agregar sustitutos válidos (excepto el primero que ya se mostró)
            for i, (nombre, score, just) in enumerate(resultado['validos'][1:], 1):
                tree.insert('', tk.END, values=(nombre, f"{score:.1f}", "Sustituto directo"))
            
            # Agregar alternativas
            for nombre, score, just in resultado['alternativas']:
                tree.insert('', tk.END, values=(nombre, f"{score:.1f}", "Alternativa terapéutica"))
            
            tree.pack(fill=tk.X, pady=5)
            
            # Scrollbar para el treeview
            scrollbar_tree = ttk.Scrollbar(frame_otras, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar_tree.set)
            scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)
    
    def mostrar_estadisticas(self, tiempo_actual):
        """Muestra estadísticas de tiempo"""
        frame_stats = ttk.LabelFrame(self.scrollable_resultados, text="📊 Estadísticas", padding=15)
        frame_stats.pack(fill=tk.X, padx=10, pady=10)
        
        stats_text = f"⌛ Tiempo de procesamiento: {tiempo_actual:.3f} segundos"
        
        if len(self.tiempos) >= 2:
            promedio = sum(self.tiempos) / len(self.tiempos)
            stats_text += f"\n🔢 Tiempo promedio ({len(self.tiempos)} consultas): {promedio:.3f} segundos"
        
        ttk.Label(frame_stats, text=stats_text, font=('Arial', 10)).pack(anchor=tk.W)
    
    def mostrar_sin_opciones(self):
        """Muestra mensaje cuando no hay opciones válidas"""
        for widget in self.scrollable_resultados.winfo_children():
            widget.destroy()
            
        ttk.Label(self.scrollable_resultados, 
                 text="❌ No se encontraron opciones válidas de sustitución",
                 font=('Arial', 14), foreground='red').pack(pady=50)
        
        self.notebook.select(1)
        self.status_label.config(text="Sin opciones válidas encontradas")
    
    def mostrar_error(self, error_msg):
        """Muestra errores de procesamiento"""
        self.progress.stop()
        self.btn_procesar.config(state='normal')
        self.status_label.config(text="Error en el procesamiento")
        messagebox.showerror("Error", f"Error durante el procesamiento:\n{error_msg}")
    
    def mostrar_analisis_detallado(self):
        """Abre ventana con análisis detallado"""
        if not self.resultado_actual:
            messagebox.showwarning("Advertencia", "No hay resultados para mostrar análisis detallado")
            return
        
        # Crear ventana de análisis detallado
        ventana_detalle = tk.Toplevel(self.root)
        ventana_detalle.title("Análisis Detallado")
        ventana_detalle.geometry("1000x600")
        
        # Crear scrolled text para mostrar análisis completo
        text_detalle = scrolledtext.ScrolledText(ventana_detalle, wrap=tk.WORD, font=('Courier', 10))
        text_detalle.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Generar contenido detallado
        contenido = self.generar_analisis_detallado()
        text_detalle.insert(tk.END, contenido)
        text_detalle.config(state=tk.DISABLED)
    
    def generar_analisis_detallado(self):
        """Genera el contenido del análisis detallado incluyendo composición."""
        resultado = self.resultado_actual
        df_info   = self.datos['df_info']

        contenido = f"""
    ANÁLISIS DETALLADO - SISTEMA EXPERTO DE SUSTITUCIÓN DE MEDICAMENTOS
    {"="*80}

    MEDICAMENTO ACTUAL:
    - Nombre: {resultado['medicamento']}
    - Composición: {resultado['composicion']}
    - Clase Terapéutica: {resultado['clase']}
    - Componente Principal: {resultado['componente']}

    EVALUACIÓN DE SUSTITUTOS:
    {"-"*40}
    """

        # Sustitutos evaluados
        for i, (nombre, score, justificacion) in enumerate(resultado['sustitutos'], 1):
            # Buscamos la composición en df_info (si no existe, marcamos como 'No disponible')
            try:
                comp = df_info.loc[
                    df_info['medicamento'].str.lower() == nombre.lower(),
                    'composicion'
                ].iloc[0]
            except Exception:
                comp = 'No disponible'

            contenido += (
                f"\n {i}. (Score: {score:.2f})  {nombre} \n"
                f"   Composición: {comp}\n"
                f"   Justificación: {justificacion}\n"
            )

        # Alternativas terapéuticas
        if resultado['alternativas']:
            contenido += f"\nALTERNATIVAS TERAPÉUTICAS:\n{'-'*40}\n"
            for i, (nombre, score, justificacion) in enumerate(resultado['alternativas'], 1):
                try:
                    comp = df_info.loc[
                        df_info['medicamento'].str.lower() == nombre.lower(),
                        'composicion'
                    ].iloc[0]
                except Exception:
                    comp = 'No disponible'

                contenido += (
                    f"\n {i}.(Score: {score:.2f}) {nombre} \n"
                    f"   Composición: {comp}\n"
                    f"   Justificación: {justificacion}\n"
                )

        return contenido


    
    def nueva_consulta(self):
        """Limpia los campos para una nueva consulta"""
        # Limpiar campos de entrada
        self.entry_sintomas.delete("1.0", tk.END)
        self.entry_historia.delete("1.0", tk.END)
        self.entry_alergias.delete(0, tk.END)
        self.entry_alergias.insert(0, "ninguna")
        self.entry_diagnostico.delete(0, tk.END)
        self.entry_medicamento.delete(0, tk.END)
        
        # Resetear variables
        self.var_motivo.set("alergia")
        self.resultado_actual = None
        
        # Limpiar resultados
        for widget in self.scrollable_resultados.winfo_children():
            widget.destroy()
        
        self.label_resultados = ttk.Label(self.scrollable_resultados, 
                                         text="Los resultados aparecerán aquí después del análisis...",
                                         font=('Arial', 12))
        self.label_resultados.pack(pady=50)
        
        # Resetear botones
        self.btn_procesar.config(state='disabled')
        self.btn_detallado.config(state='disabled')
        
        # Volver a pestaña de ingreso
        self.notebook.select(0)
        self.status_label.config(text="Listo para nueva consulta")
    
    def salir(self):
        """Cierra la aplicación"""
        if messagebox.askokcancel("Salir", "¿Está seguro que desea salir del sistema?"):
            self.root.quit()
    
    # Métodos auxiliares (mantén tus funciones originales)
    def limpiar_y_convertir(self, valor):
        """Convierte valores a string y limpia NaN/None, manteniendo números como números"""
        if pd.isna(valor):
            return ""
        try:
            return float(valor) if str(valor).replace('.', '', 1).isdigit() else str(valor).strip()
        except:
            return str(valor).strip()
    
    def limpiar_dataframe(self, df):
        """Limpia un dataframe manteniendo los tipos numéricos donde sea posible"""
        for col in df.columns:
            if df[col].dtype == object:  # Solo para columnas de texto
                df[col] = df[col].apply(lambda x: self.limpiar_y_convertir(x))
        return df

    def procesar_medicamento(self, med_input, notas, diagnostico, datos, razon=None):
        """
        Procesa el medicamento considerando la razón (alergia/desabastecimiento)
        """
        # Limpieza previa de datos manteniendo tipos numéricos
        if 'df_info' in datos and hasattr(datos['df_info'], 'copy'):
            datos['df_info'] = self.limpiar_dataframe(datos['df_info'])
        if 'df_sust' in datos and hasattr(datos['df_sust'], 'copy'):
            datos['df_sust'] = self.limpiar_dataframe(datos['df_sust'])
        
        # Obtener información del medicamento actual
        resultados = procesar_medicamento_actual(med_input, datos['df_sust'], datos['df_info'])
        
        # Si no se encontró el medicamento
        if not resultados[0]:
            return {
                "status": "error",
                "message": "No se encontró información del medicamento ingresado"
            }
        
        med_act_en, med_act_es, clase_act, review_act, composicion_act, comp_principal = resultados
        
        # Obtener los pares de sustitutos
        sust_pairs = obtener_pares_sustitutos(med_act_en, datos['df_sust'])
        en_orden = []
        
        # Evaluar cada sustituto considerando la razón
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
        
        # Filtrar válidos
        validos = [c for c in en_orden 
                    if "❌ Alergia detectada" not in c[2] 
                    and "⚠️ Información no encontrada" not in c[2]]
        
        # Buscar alternativas adicionales
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
            'razon_sustitucion': razon
        }
        
        return response

    def ejecutar(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()


# Función principal para ejecutar la aplicación
def main():
    """Función principal que ejecuta la aplicación GUI"""
    try:
        # Crear y ejecutar la aplicación
        app = SistemaMedicamentosGUI()
        app.ejecutar()
        
    except Exception as e:
        messagebox.showerror("Error Crítico", 
                           f"Error al inicializar la aplicación:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()