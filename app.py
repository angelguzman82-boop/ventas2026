import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestión Comercial", layout="wide")

st.title("📊 Gestión Comercial por Provincia")

archivo = st.file_uploader("Sube el Excel de ventas", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    df.columns = df.columns.str.strip()

    st.write("Columnas detectadas:", df.columns)

    # --- DETECCIÓN AUTOMÁTICA DE COLUMNAS ---
    cliente_col = None
    provincia_col = None
    fecha_col = None
    kw_col = None
    nombre_col = None
    apellido_col = None
    email_col = None
    telefono_col = None

    for col in df.columns:
        col_lower = col.lower()

        if "cliente" in col_lower:
            cliente_col = col
        if "provincia" in col_lower:
            provincia_col = col
        if "fecha" in col_lower:
            fecha_col = col
        if "kw" in col_lower:
            kw_col = col
        if "nombre" in col_lower:
            nombre_col = col
        if "apellido" in col_lower:
            apellido_col = col
        if "mail" in col_lower or "correo" in col_lower:
            email_col = col
        if "tel" in col_lower or "movil" in col_lower:
            telefono_col = col

    if not all([cliente_col, provincia_col, fecha_col, kw_col]):
        st.error("No se detectaron correctamente las columnas necesarias.")
        st.stop()

    # Convertir fecha
    df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")

    # Crear nombre completo
    if nombre_col and apellido_col:
        df["Nombre completo"] = (
            df[nombre_col].fillna("").astype(str) + " " +
            df[apellido_col].fillna("").astype(str)
        )
    else:
        df["Nombre completo"] = "No disponible"

    # --- AGRUPAR DATOS ---
    ventas = (
        df.groupby([cliente_col, provincia_col, fecha_col])
        .agg(volumen_total=(kw_col, "sum"))
        .reset_index()
    )

    resumen = (
        ventas.groupby([cliente_col, provincia_col])
        .agg(
            volumen_total=("volumen_total", "sum"),
            numero_compras=(fecha_col, "count"),
            ultima_compra=(fecha_col, "max")
        )
        .reset_index()
    )

    # Añadir datos de contacto (tomamos el primero disponible por cliente)
    contactos = (
        df.groupby(cliente_col)
        .agg(
            nombre=("Nombre completo", "first"),
            email=(email_col, "first") if email_col else ("Nombre completo", "first"),
            telefono=(telefono_col, "first") if telefono_col else ("Nombre completo", "first")
        )
        .reset_index()
    )

    # Unir resumen con contactos
    resultado = resumen.merge(contactos, on=cliente_col, how="left")

    provincias = sorted(resultado[provincia_col].dropna().unique())

    if provincias:
        provincia = st.selectbox("Selecciona Provincia", provincias)

        tabla = resultado[resultado[provincia_col] == provincia]

        # Ordenar por volumen
        tabla = tabla.sort_values(by="volumen_total", ascending=False)

        # Seleccionar columnas finales a mostrar
        columnas_finales = [
            cliente_col,
            "nombre",
            "email",
            "telefono",
            "volumen_total",
            "numero_compras",
            "ultima_compra"
        ]

        st.subheader("Clientes y Contactos")
        st.dataframe(tabla[columnas_finales], use_container_width=True)
