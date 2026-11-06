"""Operaciones Unitarias — aplicación principal."""

import streamlit as st

from vistas import intercambiador

st.set_page_config(
    page_title="Operaciones Unitarias",
    page_icon="⚗️",
    layout="wide",
)

MODULOS = {
    "Intercambiador de calor (LMTD / ε-NTU)": intercambiador.render,
}

st.sidebar.title("⚗️ Operaciones Unitarias")
seleccion = st.sidebar.selectbox("Módulo", list(MODULOS))
st.sidebar.caption("Diseño y simulación de equipos · v0.1.0")

MODULOS[seleccion]()
