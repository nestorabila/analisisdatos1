"""Lectura y presentación de datos desde distintos formatos."""

import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path

import pandas as pd


class LectorDatos:
  

    def __init__(self, root, area_resultados, etiqueta_archivo, mostrar_mensaje):
        self.root = root
        self.area_resultados = area_resultados
        self.etiqueta_archivo = etiqueta_archivo
        self.mostrar_mensaje = mostrar_mensaje

    def cargar_datos(self) -> Path | None:
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de datos",
            filetypes=[
                ("Archivos Excel", "*.xlsx *.xls *.xlsm *.xltx"),
            ],
        )
        if not ruta:
            return None

        archivo = Path(ruta)
        try:
            hojas = leer_excel(archivo)
        except Exception as error:
            self.etiqueta_archivo.configure(text="No se pudo cargar el archivo", fg="#b42318")
            detalle = str(error)
            if archivo.suffix.lower() == ".xls":
                detalle += "\n\nPara archivos .xls antiguos, instala el lector xlrd: pip install xlrd"
            self.mostrar_mensaje(f"No se pudo leer el contenido del archivo Excel.\n\nDetalle: {detalle}")
            return None

        self.etiqueta_archivo.configure(text=f"Archivo cargado: {archivo.name}", fg="#2457a7")
        try:
            mostrar_tablas(self.area_resultados, hojas, self.root)
        except Exception as error:
            self.mostrar_mensaje(f"El archivo se leyó, pero no se pudo mostrar la tabla.\n\nDetalle: {error}")
            return None
        return archivo


def leer_excel(ruta) -> dict:
    """Lee todas las hojas conservando las filas tal como aparecen en Excel."""
    return pd.read_excel(ruta, sheet_name=None, header=None)


def mostrar_tablas(area_resultados: tk.Widget, hojas: dict, root: tk.Tk) -> None:
    """Muestra las hojas del libro en tablas con pestañas y scroll."""
    for widget in area_resultados.winfo_children():
        widget.destroy()
    if not hojas:
        tk.Label(area_resultados, text="El archivo no contiene hojas.", bg="#ffffff").pack(anchor="nw")
        return

    estilo = ttk.Style()
    estilo.configure(
        "Excel.Treeview", font=("Segoe UI", 9), rowheight=27,
        background="#ffffff", fieldbackground="#ffffff", foreground="#344054",
    )
    estilo.configure(
        "Excel.Treeview.Heading", font=("Segoe UI", 9, "bold"),
        background="#eaf0f7", foreground="#172b4d", relief="flat",
    )
    estilo.map("Excel.Treeview", background=[("selected", "#d6e7ff")])

    pestañas = ttk.Notebook(area_resultados)
    pestañas.pack(fill="both", expand=True)
    for nombre, datos in hojas.items():
        marco = tk.Frame(pestañas, bg="#ffffff")
        pestañas.add(marco, text=str(nombre))
        filas, cantidad_columnas = datos.shape
        tk.Label(
            marco, text=f"{filas} filas  ·  {cantidad_columnas} columnas",
            font=("Segoe UI", 9), fg="#637083", bg="#ffffff",
            anchor="w", padx=8, pady=6,
        ).pack(fill="x")

        if cantidad_columnas == 0:
            tk.Label(marco, text="Esta hoja está vacía.", bg="#ffffff").pack(pady=16)
            continue

        zona_tabla = tk.Frame(marco, bg="#ffffff")
        zona_tabla.pack(fill="both", expand=True)
        columnas = [_nombre_columna(i) for i in range(cantidad_columnas)]
        tabla = ttk.Treeview(
            zona_tabla, columns=columnas, show="headings",
            selectmode="extended", style="Excel.Treeview",
        )
        tabla.bind("<Control-c>", _copiar_filas(root))
        tabla.bind("<Control-C>", _copiar_filas(root))
        barra_vertical = ttk.Scrollbar(zona_tabla, orient="vertical", command=tabla.yview)
        barra_horizontal = ttk.Scrollbar(zona_tabla, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=barra_vertical.set, xscrollcommand=barra_horizontal.set)

        for columna in columnas:
            tabla.heading(columna, text=columna)
            tabla.column(columna, width=130, minwidth=80, anchor="w", stretch=False)
        for indice, fila in enumerate(datos.itertuples(index=False, name=None), start=1):
            valores = ["" if pd.isna(valor) else str(valor) for valor in fila]
            tabla.insert("", "end", iid=str(indice), values=valores)

        tabla.grid(row=0, column=0, sticky="nsew")
        barra_vertical.grid(row=0, column=1, sticky="ns")
        barra_horizontal.grid(row=1, column=0, sticky="ew")
        zona_tabla.rowconfigure(0, weight=1)
        zona_tabla.columnconfigure(0, weight=1)


def _nombre_columna(indice: int) -> str:
    nombre = ""
    while indice >= 0:
        indice, resto = divmod(indice, 26)
        nombre = chr(65 + resto) + nombre
        indice -= 1
    return nombre


def _copiar_filas(root: tk.Tk):
    def copiar(event: tk.Event) -> str:
        tabla = event.widget
        filas = [
            "\t".join(str(valor) for valor in tabla.item(iid, "values"))
            for iid in tabla.selection()
        ]
        if filas:
            root.clipboard_clear()
            root.clipboard_append("\n".join(filas))
        return "break"

    return copiar
