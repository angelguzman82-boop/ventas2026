import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestión Comercial", layout="wide")

st.title("📊 Gestión Comercial por Provincia")

archivo = st.file_uploader("Sube el Excel de ventas", type=["xlsx"])

if archivo is not None:

    # -------- CARGA --------
    try:
        df = pd.read_excel(archivo)
    except Exception as e:
        st.error("Error al leer el archivo.")
        st.stop()

    # Limpieza básica de columnas
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace("\n", " ", regex=True)

    st.write("Columnas detectadas:")
    st.write(df.columns.tolist())

    # -------- DETECCIÓN AUTOMÁTICA --------
    columnas = {col.lower(): col for col in df.columns}

    def buscar_columna(palabras_clave):
        for col_lower, col_original in columnas.items():
            if any(p in col_lower for p in palabras_clave):
                return col_original
        return None

    cliente_col   = buscar_columna(["cliente"])
    provincia_col = buscar_columna(["prov"])
    fecha_col     = buscar_columna(["fecha"])
    kw_col        = buscar_columna(["kw"])
    nombre_col    = buscar_columna(["nombre"])
    apellido_col  = buscar_columna(["apellido"])
    email_col     = buscar_columna(["mail", "correo"])
    telefono_col  = buscar_columna(["tel", "movil"])

    # -------- VALIDACIÓN --------
    obligatorias = [cliente_col, provincia_col, fecha_col, kw_col]

    if any(col is None for col in obligatorias):
        st.error("Faltan columnas obligatorias: Cliente, Provincia, Fecha o kW.")
        st.stop()

    # -------- LIMPIEZA --------
    df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
    df[kw_col] = pd.to_numeric(df[kw_col], errors="coerce").fillna(0)

    df[cliente_col] = df[cliente_col].astype(str).str.strip()
    df[provincia_col] = df[provincia_col].astype(str).str.strip()

    # -------- NOMBRE COMPLETO --------
    if nombre_col and apellido_col:
        df["Nombre"] = (
            df[nombre_col].fillna("").astype(str).str.strip() + " " +
            df[apellido_col].fillna("").astype(str).str.strip()
        ).str.strip()
    else:
        df["Nombre"] = ""

    df["Email"] = df[email_col] if email_col else ""
    df["Teléfono"] = df[telefono_col] if telefono_col else ""

    # -------- AGRUPAR POR FACTURA (Cliente + Fecha) --------
    ventas = (
        df.groupby([cliente_col, provincia_col, fecha_col])[kw_col]
        .sum()
        .reset_index(name="volumen_total")
    )

    # -------- RESUMEN POR CLIENTE --------
    resumen = (
        ventas.groupby([cliente_col, provincia_col])
        .agg(
            volumen_total=("volumen_total", "sum"),
            numero_compras=(fecha_col, "count"),
            ultima_compra=(fecha_col, "max")
        )
        .reset_index()
    )

    # -------- CONTACTO --------
    contactos = (
        df.groupby(cliente_col)
        .first()
        .reset_index()[[cliente_col, "Nombre", "Email", "Teléfono"]]
    )

    # -------- UNIÓN FINAL --------
    resultado = resumen.merge(contactos, on=cliente_col, how="left")

    # -------- PROVINCIAS SEGURAS --------
    provincias = (
        resultado[provincia_col]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    provincias = sorted(provincias)

    if len(provincias) == 0:
        st.warning("No hay provincias disponibles.")
        st.stop()

    # -------- SELECTOR --------
    provincia_sel = st.selectbox("Selecciona Provincia", provincias)

    tabla = resultado[resultado[provincia_col] == provincia_sel]
    tabla = tabla.sort_values(by="volumen_total", ascending=False)

    # -------- MÉTRICAS --------
    col1, col2, col3 = st.columns(3)

    col1.metric("Clientes", len(tabla))
    col2.metric("Volumen Total kW", round(tabla["volumen_total"].sum(), 2))
    col3.metric("Media por Cliente", round(tabla["volumen_total"].mean(), 2) if len(tabla) > 0 else 0)

    # -------- TABLA --------
    st.subheader("Clientes y Contactos")
    st.dataframe(tabla, use_container_width=True)
