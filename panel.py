"""Interfaz inicial para la aplicación de análisis de datos."""

import tkinter as tk
from tkinter import ttk
from threading import Thread
import re

from interpretar import analizar_excel
from leerdatos import LectorDatos
from limpiardatos import limpiar_excel
from visualizardatos import graficar


class PanelAnalisis:
    """Ventana principal con controles y un área para mostrar resultados."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ANÁLISIS DE DATOS")
        self.root.geometry("1000x680")
        self.root.minsize(760, 520)
        self.root.configure(bg="#f3f5f8")

        self.archivo_datos = None
        self._crear_interfaz()
        self.lector_datos = LectorDatos(
            self.root, self.area_resultados, self.etiqueta_archivo, self._mostrar_mensaje
        )

    def _crear_interfaz(self) -> None:
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "Accion.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 12),
            foreground="#ffffff",
            background="#2457a7",
            borderwidth=0,
        )
        estilo.map("Accion.TButton", background=[("active", "#194682")])

        contenedor = tk.Frame(self.root, bg="#f3f5f8", padx=30, pady=26)
        contenedor.pack(fill="both", expand=True)

        tk.Label(
            contenedor,
            text="ANÁLISIS DE DATOS",
            font=("Segoe UI", 23, "bold"),
            fg="#172b4d",
            bg="#f3f5f8",
        ).pack(anchor="w")
        tk.Label(
            contenedor,
            text="Carga un archivo de datos y consulta aquí su contenido y resultados.",
            font=("Segoe UI", 11),
            fg="#637083",
            bg="#f3f5f8",
        ).pack(anchor="w", pady=(5, 20))

        acciones = tk.Frame(contenedor, bg="#f3f5f8")
        acciones.pack(fill="x", pady=(0, 20))
        botones = (
            ("EXTRAER DATOS", self._cargar_datos),
            ("LIMPIAR DATOS", self._limpiar_datos),
            ("GRAFICAR DATOS", lambda: graficar(self.area_resultados, self.archivo_datos)),
            ("INTERPRETAR DATOS", self._interpretar_datos),
        )
        self.boton_extraer = None
        self.boton_interpretar = None
        for columna, (texto, comando) in enumerate(botones):
            acciones.columnconfigure(columna, weight=1, uniform="boton")
            boton = ttk.Button(
                acciones, text=texto, style="Accion.TButton", command=comando
            )
            boton.grid(row=0, column=columna, sticky="ew", padx=(0 if columna == 0 else 6, 0 if columna == 3 else 6))
            if columna == 0:
                self.boton_extraer = boton
            elif columna == 3:
                self.boton_interpretar = boton

        salida = tk.Frame(contenedor, bg="#ffffff", highlightbackground="#dce2ea", highlightthickness=1)
        salida.pack(fill="both", expand=True)
        encabezado = tk.Frame(salida, bg="#ffffff", padx=18, pady=14)
        encabezado.pack(fill="x")
        tk.Label(
            encabezado,
            text="RESULTADOS",
            font=("Segoe UI", 12, "bold"),
            fg="#172b4d",
            bg="#ffffff",
        ).pack(anchor="w")
        self.etiqueta_archivo = tk.Label(
            encabezado,
            text="Ningún archivo cargado",
            font=("Segoe UI", 9),
            fg="#718096",
            bg="#ffffff",
        )
        self.etiqueta_archivo.pack(anchor="w", pady=(4, 0))
        tk.Frame(salida, bg="#e8edf3", height=1).pack(fill="x")

        self.area_resultados = tk.Frame(salida, bg="#ffffff", padx=18, pady=14)
        self.area_resultados.pack(fill="both", expand=True)
        self._mostrar_mensaje("Aquí aparecerán los resultados de las operaciones.")

    def _cargar_datos(self) -> None:
        self.archivo_datos = self.lector_datos.cargar_datos()

    def _limpiar_datos(self) -> None:
        if self.archivo_datos is None:
            self._mostrar_mensaje("Primero selecciona un archivo con el botón EXTRAER DATOS.")
            return
        try:
            informe, self.archivo_datos = limpiar_excel(self.archivo_datos)
        except Exception as error:
            self._mostrar_mensaje(f"No se pudo limpiar el archivo.\n\nDetalle: {error}")
            return
        self._mostrar_resultado_formateado(informe)

    def _interpretar_datos(self) -> None:
        if self.archivo_datos is None:
            self._mostrar_mensaje("Primero selecciona un archivo con el botón EXTRAER DATOS.")
            return

        archivo = self.archivo_datos
        self.boton_extraer.configure(state="disabled")
        self.boton_interpretar.configure(state="disabled")
        self._mostrar_mensaje("Enviando los datos del Excel a Gemini. Espera un momento...")
        Thread(target=self._ejecutar_analisis, args=(archivo,), daemon=True).start()

    def _ejecutar_analisis(self, archivo) -> None:
        try:
            resultado = analizar_excel(archivo)
            error = None
        except Exception as excepcion:
            resultado = None
            error = str(excepcion)
        self.root.after(0, self._mostrar_resultado_analisis, resultado, error)

    def _mostrar_resultado_analisis(self, resultado: str | None, error: str | None) -> None:
        self.boton_extraer.configure(state="normal")
        self.boton_interpretar.configure(state="normal")
        if error:
            self._mostrar_mensaje(f"No se pudo interpretar el archivo.\n\nDetalle: {error}")
        else:
            self._mostrar_resultado_formateado(resultado)

    def _limpiar_area_resultados(self) -> None:
        for widget in self.area_resultados.winfo_children():
            widget.destroy()

    def _pendiente(self, operacion: str) -> None:
        if self.archivo_datos is None:
            self._mostrar_mensaje("Primero selecciona un archivo con el botón EXTRAER DATOS.")
            return
        self._mostrar_mensaje(f"{operacion}: esta opción está preparada en la interfaz y se implementará después.")

    def _mostrar_mensaje(self, texto: str) -> None:
        self._limpiar_area_resultados()
        cuadro = tk.Text(
            self.area_resultados,
            wrap="word",
            font=("Segoe UI", 10),
            fg="#344054",
            bg="#ffffff",
            relief="flat",
            borderwidth=0,
            padx=4,
            pady=4,
            height=8,
        )
        cuadro.pack(fill="both", expand=True, anchor="nw")
        cuadro.insert("1.0", texto)
        cuadro.configure(state="disabled")
        cuadro.bind("<Control-c>", self._copiar_seleccion_texto)
        cuadro.bind("<Control-C>", self._copiar_seleccion_texto)

    def _mostrar_resultado_formateado(self, texto: str) -> None:
        self._limpiar_area_resultados()
        cuadro = tk.Text(
            self.area_resultados,
            wrap="word",
            font=("Segoe UI", 10),
            fg="#344054",
            bg="#ffffff",
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=6,
            spacing1=3,
            spacing3=7,
        )
        cuadro.pack(fill="both", expand=True, anchor="nw")
        cuadro.tag_configure("titulo", font=("Segoe UI", 15, "bold"), foreground="#174ea6", spacing1=5, spacing3=12)
        cuadro.tag_configure("subtitulo", font=("Segoe UI", 11, "bold"), foreground="#087e8b", spacing1=10, spacing3=5)
        cuadro.tag_configure("resaltado", font=("Segoe UI", 10, "bold"), foreground="#a34a00")

        lineas = texto.splitlines()
        primera_linea = True
        for linea in lineas:
            limpia = linea.strip()
            if not limpia:
                cuadro.insert("end", "\n")
                continue

            if limpia.startswith("### ") or limpia.startswith("## "):
                cuadro.insert("end", limpia.lstrip("# ") + "\n", "subtitulo")
                primera_linea = False
                continue
            if limpia.startswith("# "):
                cuadro.insert("end", limpia[2:] + "\n", "titulo")
                primera_linea = False
                continue
            if primera_linea and len(limpia) < 100:
                cuadro.insert("end", limpia + "\n", "titulo")
                primera_linea = False
                continue

            partes = re.split(r"(\*\*.+?\*\*)", linea)
            for parte in partes:
                if parte.startswith("**") and parte.endswith("**"):
                    cuadro.insert("end", parte[2:-2], "resaltado")
                else:
                    cuadro.insert("end", parte)
            cuadro.insert("end", "\n")
            primera_linea = False

        cuadro.configure(state="disabled")
        cuadro.bind("<Control-c>", self._copiar_seleccion_texto)
        cuadro.bind("<Control-C>", self._copiar_seleccion_texto)

    def _copiar_seleccion_texto(self, evento: tk.Event) -> str:
        widget = evento.widget
        try:
            texto = widget.get("sel.first", "sel.last")
        except tk.TclError:
            return "break"
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        return "break"

def ejecutar() -> None:
    root = tk.Tk()
    PanelAnalisis(root)
    root.mainloop()