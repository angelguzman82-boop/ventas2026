import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestión Comercial", layout="wide")

st.title("📊 Gestión Comercial por Provincia")

archivo = st.file_uploader("Sube el Excel de ventas", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)

    # Limpiar nombres de columnas (espacios invisibles)
    df.columns = df.columns.str.strip()

    st.write("Columnas detectadas:", df.columns)

    # -------- DETECCIÓN FLEXIBLE DE COLUMNAS --------
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

    # Verificación obligatoria
    if not cliente_col:
        st.error("No se detectó columna Cliente")
        st.stop()

    if not provincia_col:
        st.error("No se detectó columna Provincia")
        st.stop()

    if not fecha_col:
        st.error("No se detectó columna Fecha")
        st.stop()

    if not kw_col:
        st.error("No se detectó columna kW")
        st.stop()

    # -------- LIMPIEZA DE DATOS --------

    df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
    df[kw_col] = pd.to_numeric(df[kw_col], errors="coerce").fillna(0)

    # Crear nombre completo
    if nombre_col and apellido_col:
        df["Nombre completo"] = (
            df[nombre_col].fillna("").astype(str) + " " +
            df[apellido_col].fillna("").astype(str)
        )
    else:
        df["Nombre completo"] = "No disponible"

    # -------- AGRUPAR VENTAS --------

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

    # -------- DATOS DE CONTACTO --------

    contactos_dict = {
        cliente_col: cliente_col,
        "Nombre": ("Nombre completo", "first")
    }

    if email_col:
        contactos_dict["Email"] = (email_col, "first")
    else:
        df["Email_tmp"] = ""
        contactos_dict["Email"] = ("Email_tmp", "first")

    if telefono_col:
        contactos_dict["Teléfono"] = (telefono_col, "first")
    else:
        df["Tel_tmp"] = ""
        contactos_dict["Teléfono"] = ("Tel_tmp", "first")

    contactos = (
        df.groupby(cliente_col)
        .agg(**contactos_dict)
        .reset_index()
    )

    # -------- UNIR TODO --------

    resultado = resumen.merge(contactos, on=cliente_col, how="left")

    provincias = sorted(resultado[provincia_col].dropna().unique())

    if not provincias:
        st.warning("No hay provincias disponibles")
        st.stop()

    provincia_sel = st.selectbox("Selecciona Provincia", provincias)

    tabla = resultado[resultado[provincia_col] == provincia_sel]
    tabla = tabla.sort_values(by="volumen_total", ascending=False)

    columnas_mostrar = [
        cliente_col,
        "Nombre",
        "Email",
        "Teléfono",
        "volumen_total",
        "numero_compras",
        "ultima_compra"
    ]

    st.subheader("Clientes y Contactos")
    st.dataframe(tabla[columnas_mostrar], use_container_width=True)
