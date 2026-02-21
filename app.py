import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestión Comercial", layout="wide")

st.title("📊 Gestión Comercial por Provincia")

archivo = st.file_uploader("Sube el Excel de ventas", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    df.columns = df.columns.str.strip()

    st.write("Columnas detectadas:", df.columns)

    # -------- DETECCIÓN DE COLUMNAS --------
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
        if "prov" in col_lower:
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

    # Validaciones mínimas
    if not cliente_col or not provincia_col or not fecha_col or not kw_col:
        st.error("Faltan columnas obligatorias (Cliente, Provincia, Fecha o kW).")
        st.stop()

    # -------- LIMPIEZA --------
    df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
    df[kw_col] = pd.to_numeric(df[kw_col], errors="coerce").fillna(0)

    # Nombre completo
    if nombre_col and apellido_col:
        df["Nombre"] = (
            df[nombre_col].fillna("").astype(str) + " " +
            df[apellido_col].fillna("").astype(str)
        )
    else:
        df["Nombre"] = ""

    if email_col:
        df["Email"] = df[email_col]
    else:
        df["Email"] = ""

    if telefono_col:
        df["Teléfono"] = df[telefono_col]
    else:
        df["Teléfono"] = ""

    # -------- AGRUPAR VENTAS --------
    ventas = (
        df.groupby([cliente_col, provincia_col, fecha_col])[kw_col]
        .sum()
        .reset_index(name="volumen_total")
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

    # -------- CONTACTO (primer registro por cliente) --------
    contactos = (
        df.groupby(cliente_col)
        .first()
        .reset_index()
        [[cliente_col, "Nombre", "Email", "Teléfono"]]
    )

    # -------- UNIR TODO --------
    resultado = resumen.merge(contactos, on=cliente_col, how="left")

    provincias = sorted(resultado[provincia_col].dropna().unique())

    if not provincias:
        st.warning("No hay provincias disponibles.")
        st.stop()

    provincia_sel = st.selectbox("Selecciona Provincia", provincias)

    tabla = resultado[resultado[provincia_col] == provincia_sel]
    tabla = tabla.sort_values(by="volumen_total", ascending=False)

    st.subheader("Clientes y Contactos")
    st.dataframe(tabla, use_container_width=True)
