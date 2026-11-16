"""Exporta a PDF las preguntas, tablas y gráficos, con una narración de datos hecha por IA."""

from io import BytesIO
from tkinter import filedialog, messagebox

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from interpretar import _leer_env, _llamar_gemini

# Narración de datos: lo que la IA debe contar en cada pregunta
INSTRUCCION = ("Eres analista de datos. Narra en español, en un párrafo de 3 a 4 oraciones, sin títulos ni viñetas, "
               "usando solo las cifras de la tabla y sin inventar datos. Copia cada cifra de la fila que le corresponde "
               "y no menciones lo que la tabla no contiene.")
PROMPTS = {
    "1": "Compara venta neta, utilidad y margen: quién vende más, quién gana más y quién tiene el margen más bajo.",
    "2": "Indica dónde se concentran los montos y qué parte del total representa el mayor.",
    "3": "Indica cuánto hay por cobrar en total y qué sucursal concentra la mayor parte.",
    "4": "Indica si algún producto tiene utilidad negativa y en qué semestre ocurre.",
    "5": "Describe los meses más altos y más bajos y cuáles son las temporadas clave.",
}


def narrar(pregunta, titulo, tabla):
    env = _leer_env()
    texto = f"{INSTRUCCION}\nPregunta: {pregunta}\n{PROMPTS[pregunta[0]]}\n\n{titulo}:\n{tabla.to_string()}"
    try:
        return _llamar_gemini(env["GEMINI_MODEL"], env["GEMINI_API_KEY"], texto)
    except Exception as error:
        return f"No se pudo generar la narración: {error}"


def tabla_pdf(tabla):
    filas = [[tabla.index.name or ""] + list(tabla.columns)]
    for indice, fila in tabla.iterrows():
        filas.append([" – ".join(indice) if isinstance(indice, tuple) else indice] + [f"{x:,.1f}" for x in fila])
    t = Table(filas, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2457a7")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                           ("FONTSIZE", (0, 0), (-1, -1), 8)]))
    return t


def grafico_pdf(figura):
    imagen = BytesIO()
    figura.savefig(imagen, format="png", dpi=150)
    imagen.seek(0)
    return Image(imagen, width=17 * cm, height=7.4 * cm)


def exportar_pdf(informe):
    ruta = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Informe_ventas.pdf",
                                        filetypes=[("PDF", "*.pdf")])
    if not ruta:
        return
    estilos = getSampleStyleSheet()
    partes = [Paragraph("Análisis de datos – Ventas 2025", estilos["Title"])]
    for pregunta, resultados in informe:
        partes.append(Paragraph(pregunta, estilos["Heading2"]))
        for titulo, tabla, figura in resultados:
            partes += [tabla_pdf(tabla), Spacer(1, 6), grafico_pdf(figura),
                       Paragraph(narrar(pregunta, titulo, tabla), estilos["BodyText"]), Spacer(1, 16)]
    SimpleDocTemplate(ruta, pagesize=A4).build(partes)
    messagebox.showinfo("Exportar PDF", f"PDF guardado en:\n{ruta}")
