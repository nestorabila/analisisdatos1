"""Limpieza de datos con pandas: vacíos, fechas, texto, montos, nombres y duplicados."""

from pathlib import Path

import numpy as np
import pandas as pd

# Un monto escrito de distintas formas: "100", "-95", "Bs 1,768.00", "Bs. 25,5", "10 bolivianos", "5%"
MONTO = r"(?i)^(?:bs\.?|bolivianos)?\s*(-?\d+(?:[.,]\d+)?)\s*(?:bs\.?|bolivianos|%)?$"

# Un mismo nombre escrito de varias formas se reconoce por una palabra clave (en orden)
NOMBRES = {
    "Sucursal": {"paz|lpz": "La Paz", "tja|tarija": "Tarija Centro",
                 "cruz|scz": "Santa Cruz", "conc": "Valle de Concepción"},
    "Producto": {"estuche|caja": "Estuche Regalo (vino + singani)", "negra": "Singani Etiqueta Negra 750 ml",
                 "patero": "Vino Patero 1 L", r"1 ?l": "Singani Clásico 1 L", "singani": "Singani Clásico 750 ml",
                 "malbec": "Vino Tinto Malbec 750 ml", "tannat": "Vino Tinto Tannat 750 ml",
                 "cab": "Vino Tinto Cabernet Sauvignon 750 ml", "moscatel": "Vino Blanco Moscatel 750 ml",
                 "rosado": "Vino Rosado 750 ml"},
}


def limpiar_excel(ruta):
    """Limpia todas las hojas, guarda <archivo>_limpio.xlsx y devuelve (informe, ruta_limpia)."""
    ruta = Path(ruta)
    ruta_limpia = ruta.with_name(ruta.stem.removesuffix("_limpio") + "_limpio.xlsx")
    hojas = {hoja: limpiar_tabla(df) for hoja, df in pd.read_excel(ruta, sheet_name=None).items()}
    completar_ventas(hojas["Ventas 2025"][0], hojas["Productos"][0])

    informe = ["# Limpieza de datos"]
    with pd.ExcelWriter(ruta_limpia) as excel:
        for hoja, (df, resumen) in hojas.items():
            df.to_excel(excel, sheet_name=hoja, index=False)
            informe += [f"## Hoja: {hoja}", *resumen]
    informe.append(f"\nArchivo limpio guardado como: **{ruta_limpia.name}**")
    return "\n".join(informe), ruta_limpia


def limpiar_tabla(df):
    filas = len(df)

    # 1. Filas vacías, filas de prueba y duplicados exactos
    df = df.dropna(how="all")
    df = df[~df.iloc[:, 0].astype(str).str.contains("prueba", case=False)]
    duplicados = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()

    # 2. Fechas escritas de distintas formas ("01/01/2025", "01-01-25" -> 2025-01-01)
    for col in [c for c in df if "fecha" in str(c).lower()]:
        df[col] = pd.to_datetime(df[col].astype(str), format="mixed", dayfirst=True, errors="coerce")

    # 3. Texto: quitar espacios y unificar mayúsculas ("  juan " -> "Juan")
    texto = df.select_dtypes("object").columns
    df[texto] = df[texto].apply(lambda col: col.astype("string").str.strip().str.title())

    # 4. Montos escritos de distintas formas ("Bs 1,768.00", "-95", "10 bs" -> número)
    convertidas = []
    for col in texto:
        sin_miles = df[col].str.replace(r",(?=\d{3}\b)", "", regex=True)
        numeros = sin_miles.str.extract(MONTO)[0].str.replace(",", ".").astype(float)
        if numeros.count() >= 0.8 * df[col].count():   # si casi todo es monto, la columna es numérica
            df[col] = numeros
            convertidas.append(col)

    # 5. Nombres escritos de varias formas -> nombre oficial ("LPZ", "la paz" -> "La Paz")
    for col in [c for c in NOMBRES if c in df]:
        df[col] = unificar(df[col], NOMBRES[col])
        df = df.dropna(subset=[col])   # quita filas sin nombre válido (notas al pie)

    # 6. Texto faltante -> "Sin dato"
    faltantes = int(df.select_dtypes("string").isna().sum().sum())
    df[df.select_dtypes("string").columns] = df.select_dtypes("string").fillna("Sin dato")

    return df, [
        f"Filas al inicio: {filas}",
        f"Filas vacías o de prueba eliminadas: **{filas - len(df) - duplicados}**",
        f"Filas duplicadas eliminadas: **{duplicados}**",
        f"Columnas convertidas a número: **{', '.join(map(str, convertidas)) or 'ninguna'}**",
        f"Textos faltantes rellenados: **{faltantes}**",
        f"Filas al final: {len(df)}",
    ]


def unificar(serie, nombres):
    texto = serie.astype(str).str.lower()
    return np.select([texto.str.contains(clave) for clave in nombres], list(nombres.values()), None)


def completar_ventas(ventas, productos):
    """Precio desde la lista oficial y cantidad vacía = Total ÷ (precio × (1 − descuento))."""
    ventas["Precio Unit. (Bs)"] = ventas["Producto"].map(productos.set_index("Producto")["Precio de lista (Bs)"])
    precio_final = ventas["Precio Unit. (Bs)"] * (1 - ventas["Descuento (%)"] / 100)
    ventas["Cantidad"] = ventas["Cantidad"].fillna(ventas["Total (Bs)"] / precio_final).round()
