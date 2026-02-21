import streamlit as st
import pandas as pd
import unicodedata

st.set_page_config(page_title="Gestión Comercial", layout="wide")

st.title("📊 Gestión Comercial por Provincia")

archivo = st.file_uploader("Sube el Excel de ventas", type=["xlsx"])

if archivo is not None:

    # -------- CARGA --------
    try:
        df = pd.read_excel(archivo)
    except:
        st.error("Error al leer el archivo Excel.")
        st.stop()

    df.columns = df.columns.str.strip().str.replace("\n", " ", regex=True)

    st.write("Columnas detectadas:")
    st.write(df.columns.tolist())

    # -------- DETECCIÓN AUTOMÁTICA DE COLUMNAS --------
    columnas = {col.lower(): col for col in df.columns}

    def buscar_columna(palabras):
        for col_lower, col_original in columnas.items():
            if any(p in col_lower for p in palabras):
                return col_original
        return None

    cliente_col   = buscar_columna(["cliente"])
    provincia_col = buscar_columna(["prov", "poblac", "ciudad"])
    fecha_col     = buscar_columna(["fecha"])
    kw_col        = buscar_columna(["kw"])
    nombre_col    = buscar_columna(["nombre"])
    apellido_col  = buscar_columna(["apellido"])
    email_col     = buscar_columna(["mail", "correo"])
    telefono_col  = buscar_columna(["tel", "movil"])

    if not cliente_col or not provincia_col or not fecha_col or not kw_col:
        st.error("Faltan columnas obligatorias (Cliente, Provincia, Fecha o kW).")
        st.stop()

    # -------- LIMPIEZA --------
    df[fecha_col] = pd.to_datetime(df[fecha_col], errors="coerce")
    df[kw_col] = pd.to_numeric(df[kw_col], errors="coerce").fillna(0)

    # -------- NORMALIZAR TEXTO --------
    def limpiar_texto(texto):
        if pd.isna(texto):
            return ""
        texto = str(texto).strip().upper()
        texto = unicodedata.normalize('NFKD', texto)
        texto = "".join([c for c in texto if not unicodedata.combining(c)])
        return texto

    df[provincia_col] = df[provincia_col].apply(limpiar_texto)
    df[cliente_col] = df[cliente_col].astype(str).str.strip()

    # -------- LISTA OFICIAL PROVINCIAS --------
    provincias_oficiales = [
        "ALAVA","ALBACETE","ALICANTE","ALMERIA","ASTURIAS","AVILA","BADAJOZ",
        "BARCELONA","BURGOS","CACERES","CADIZ","CANTABRIA","CASTELLON",
        "CIUDAD REAL","CORDOBA","CUENCA","GIRONA","GRANADA","GUADALAJARA",
        "GUIPUZCOA","HUELVA","HUESCA","ILLES BALEARS","JAEN","LA CORUNA",
        "LA RIOJA","LAS PALMAS","LEON","LLEIDA","LUGO","MADRID","MALAGA",
        "MURCIA","NAVARRA","OURENSE","PALENCIA","PONTEVEDRA","SALAMANCA",
        "SANTA CRUZ DE TENERIFE","SEGOVIA","SEVILLA","SORIA","TARRAGONA",
        "TERUEL","TOLEDO","VALENCIA","VALLADOLID","VIZCAYA","ZAMORA",
        "ZARAGOZA","CEUTA","MELILLA"
    ]

    def extraer_provincia(texto):
        for prov in provincias_oficiales:
            if prov in texto:
                return prov
        return None

    df["Provincia_Limpia"] = df[provincia_col].apply(extraer_provincia)

    # Eliminar registros sin provincia válida
    df = df[df["Provincia_Limpia"].notna()]

    if df.empty:
        st.warning("No se han podido identificar provincias válidas.")
        st.stop()

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

    # -------- AGRUPAR POR FACTURA --------
    ventas = (
        df.groupby([cliente_col, "Provincia_Limpia", fecha_col])[kw_col]
        .sum()
        .reset_index(name="volumen_total")
    )

    # -------- RESUMEN POR CLIENTE --------
    resumen = (
        ventas.groupby([cliente_col, "Provincia_Limpia"])
        .agg(
            volumen_total=("volumen_total", "sum"),
            numero_compras=(fecha_col, "count"),
            ultima_compra=(fecha_col, "max")
        )
        .reset_index()
    )

    # -------- CONTACTOS --------
    contactos = (
        df.groupby(cliente_col)
        .first()
        .reset_index()[[cliente_col, "Nombre", "Email", "Teléfono"]]
    )

    resultado = resumen.merge(contactos, on=cliente_col, how="left")

    # -------- SELECTOR PROVINCIA --------
    provincias = sorted(resultado["Provincia_Limpia"].unique())

    provincia_sel = st.selectbox("Selecciona Provincia", provincias)

    tabla = resultado[resultado["Provincia_Limpia"] == provincia_sel]
    tabla = tabla.sort_values(by="volumen_total", ascending=False)

    # -------- MÉTRICAS --------
    col1, col2, col3 = st.columns(3)

    col1.metric("Clientes", len(tabla))
    col2.metric("Volumen Total kW", round(tabla["volumen_total"].sum(), 2))
    col3.metric("Media por Cliente", round(tabla["volumen_total"].mean(), 2) if len(tabla) > 0 else 0)

    # -------- TABLA --------
    st.subheader(f"Clientes en {provincia_sel}")
    st.dataframe(tabla, use_container_width=True)
