"""Operaciones Unitarias — aplicación principal."""

import sys
from pathlib import Path

import streamlit as st

# Garantiza que los paquetes locales sean importables sin importar
# desde qué directorio lance Streamlit la app (local o Cloud).
sys.path.insert(0, str(Path(__file__).resolve().parent))

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
st.sidebar.caption("Diseño y simulación de equipos · v0.1.1")

MODULOS[seleccion]()
