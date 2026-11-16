"""Tablas y gráficos del Excel limpio, organizados por pregunta de la Gerencia."""

import tkinter as tk
from tkinter import ttk

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from exportarpdf import exportar_pdf


def leer(ruta):
    v = pd.read_excel(ruta, sheet_name="Ventas 2025")
    p = pd.read_excel(ruta, sheet_name="Productos")
    p.columns = ["Código", "Producto", "Categoría", "Precio lista", "Costo ene-jun", "Costo jul-dic"]
    v = v.merge(p, on="Producto", how="left")  # trae el costo de cada producto

    v["Semestre"] = np.where(v["Fecha"].dt.month <= 6, "Ene–jun", "Jul–dic")
    costo = np.where(v["Semestre"] == "Ene–jun", v["Costo ene-jun"], v["Costo jul-dic"])
    v["Venta neta (Bs)"] = v["Total (Bs)"]
    v["Costo (Bs)"] = v["Cantidad"] * costo
    v["Utilidad (Bs)"] = v["Total (Bs)"] - v["Costo (Bs)"]
    v["Descuentos (Bs)"] = v["Cantidad"] * v["Precio Unit. (Bs)"] - v["Total (Bs)"]
    v["Mes"] = v["Fecha"].dt.month
    return v


def resumen(v, columna):
    t = v.groupby(columna)[["Venta neta (Bs)", "Utilidad (Bs)"]].sum().sort_values("Venta neta (Bs)", ascending=False)
    t["Margen %"] = 100 * t["Utilidad (Bs)"] / t["Venta neta (Bs)"]
    t["% de la venta"] = 100 * t["Venta neta (Bs)"] / t["Venta neta (Bs)"].sum()
    return t


def preguntas(v):
    devueltas = v[v["Estado de pago"] == "Devuelto"]
    cobro = v[v["Estado de pago"].str.contains("Pendiente|Crédito")]
    bajo_costo = v[(v["Total (Bs)"] > 0) & (v["Total (Bs)"] < v["Costo (Bs)"])]   # facturas vendidas por menos de lo que costaron
    return [
        ("1. ¿Cuánto se vendió realmente en 2025 y cuánto fue la ganancia (margen) por sucursal, producto y canal de venta?", [
            ("Por sucursal", resumen(v, "Sucursal"), "bar"),
            ("Por producto", resumen(v, "Producto"), "barh"),
            ("Por canal", resumen(v, "Canal"), "bar")]),
        ("2. ¿Cuánto dinero se dejó de percibir por descuentos y por devoluciones o anulaciones? ¿Dónde se concentran?", [
            ("Descuentos por sucursal y canal", v.groupby(["Sucursal", "Canal"])[["Descuentos (Bs)"]].sum()
                .sort_values("Descuentos (Bs)", ascending=False), "barh"),
            ("Devoluciones por vendedor", devueltas.groupby(["Vendedor", "Sucursal"])["Total (Bs)"].agg(["count", "sum"])
                .set_axis(["N° registros", "Monto (Bs)"], axis=1).sort_values("Monto (Bs)"), "bar")]),
        ("3. ¿Qué monto está pendiente de cobro y en qué sucursal o canal?", [
            ("Por cobrar por sucursal", cobro.pivot_table("Total (Bs)", "Sucursal", "Estado de pago", "sum")
                .add_suffix(" (Bs)"), "bar")]),
        ("4. ¿Existe algún producto que se esté vendiendo por debajo de su costo?", [
            ("Facturas vendidas por debajo del costo", bajo_costo.groupby("Producto")[["Total (Bs)", "Costo (Bs)"]]
                .agg(["count", "sum"]).iloc[:, [0, 3, 1]].set_axis(["N° facturas", "Costo (Bs)", "Vendido en (Bs)"], axis=1), "bar")]),
        ("5. ¿Cómo se comportan las ventas mes a mes? ¿Qué temporadas son clave?", [
            ("Venta y utilidad por mes", v.groupby("Mes")[["Venta neta (Bs)", "Utilidad (Bs)"]].sum(), "line")]),
    ]


def dibujar(titulo, tabla, tipo):
    figura = Figure(figsize=(8, 3.5))
    tabla.filter(like="Bs").plot(kind=tipo, ax=figura.add_subplot(), title=titulo)
    figura.tight_layout()
    return figura


def mostrar(padre, tabla, figura):
    #devolver tablas arriba de cada grafico
    marco = tk.Frame(padre, bg="#ffffff")
    columnas = [tabla.index.name or ""] + list(tabla.columns)
    vista = ttk.Treeview(marco, columns=columnas, show="headings", height=len(tabla))
    for col in columnas:
        vista.heading(col, text=col)
    for indice, fila in tabla.iterrows():
        etiqueta = " – ".join(indice) if isinstance(indice, tuple) else indice
        vista.insert("", "end", values=[etiqueta] + [f"{x:,.1f}" for x in fila])
    vista.pack(fill="x")
    FigureCanvasTkAgg(figura, marco).get_tk_widget().pack(fill="x", pady=(4, 0))
    return marco


def graficar(area, ruta):
    if ruta is None:
        return
    for widget in area.winfo_children():
        widget.destroy()
    informe = [(pregunta, [(titulo, tabla.round(1), dibujar(titulo, tabla, tipo)) for titulo, tabla, tipo in resultados])
               for pregunta, resultados in preguntas(leer(ruta))]
    ttk.Button(area, text="EXPORTAR PDF", style="Accion.TButton",
               command=lambda: exportar_pdf(informe)).pack(anchor="e", pady=(0, 8))
    hoja = tk.Text(area, wrap="word", bg="#ffffff", relief="flat")
    barra = ttk.Scrollbar(area, command=hoja.yview)
    hoja.configure(yscrollcommand=barra.set)
    barra.pack(side="right", fill="y")
    hoja.pack(fill="both", expand=True)
    hoja.tag_configure("pregunta", font=("Segoe UI", 12, "bold"), foreground="#174ea6", spacing1=18, spacing3=8)

    for pregunta, resultados in informe:
        hoja.insert("end", pregunta + "\n", "pregunta")
        for titulo, tabla, figura in resultados:
            hoja.window_create("end", window=mostrar(hoja, tabla, figura))
            hoja.insert("end", "\n\n")
    hoja.configure(state="disabled")
