import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestión Comercial", layout="wide")

st.title("📊 Gestión Comercial por Provincia")

archivo = st.file_uploader("Sube el Excel de ventas", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)

    df.columns = df.columns.str.strip()

    df["Fecha factura"] = pd.to_datetime(df["Fecha factura"])

    df["Contacto"] = df["Nombre"] + " " + df["Apellido"]

    ventas = (
        df.groupby(["Cliente", "Provincia", "Fecha factura"])
        .agg(volumen_total=("kW", "sum"))
        .reset_index()
    )

    resumen = (
        ventas.groupby(["Cliente", "Provincia"])
        .agg(
            volumen_total=("volumen_total", "sum"),
            numero_compras=("Fecha factura", "count"),
            ultima_compra=("Fecha factura", "max")
        )
        .reset_index()
        .sort_values(by="volumen_total", ascending=False)
    )

    provincias = sorted(resumen["Provincia"].unique())
    provincia = st.selectbox("Selecciona Provincia", provincias)

    clientes = resumen[resumen["Provincia"] == provincia]

    st.subheader("Clientes")
    st.dataframe(clientes, use_container_width=True)

    cliente_sel = st.selectbox("Selecciona Cliente", clientes["Cliente"])

    if cliente_sel:
        st.divider()
        datos = clientes[clientes["Cliente"] == cliente_sel].iloc[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Volumen Total (kW)", round(datos["volumen_total"], 2))
        col2.metric("Número de Compras", int(datos["numero_compras"]))
        col3.metric("Última Compra", datos["ultima_compra"].date())

        st.subheader("Histórico de Compras")

        historial = ventas[ventas["Cliente"] == cliente_sel]
        st.dataframe(historial.sort_values(by="Fecha factura", ascending=False),
                     use_container_width=True)

        st.subheader("Contactos")

        contactos = df[df["Cliente"] == cliente_sel][
            ["Contacto", "Email", "Teléfono"]
        ].drop_duplicates()

        st.dataframe(contactos, use_container_width=True)
