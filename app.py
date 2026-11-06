"""Operaciones Unitarias — aplicación principal (todo en uno)."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import nucleo_hx as hx
import vista_3d 

st.set_page_config(
    page_title="Operaciones Unitarias",
    page_icon="⚗️",
    layout="wide",
)

# ------------------------------------------------------------- Vista HX
def render_intercambiador() -> None:
    st.header("Intercambiador de calor — LMTD y ε-NTU")

    conf = st.selectbox(
        "Configuración de flujo",
        options=list(hx.CONFIGURACIONES),
        format_func=lambda k: hx.CONFIGURACIONES[k],
    )
    modo = st.radio(
        "Modo de cálculo",
        ["Dimensionamiento (área requerida)", "Simulación (área conocida)"],
        horizontal=True,
    )

    with st.sidebar:
        st.subheader("Fluido caliente")
        m_h = st.number_input("ṁ caliente [kg/s]", 0.01, 1e4, 2.0, format="%.3f")
        cp_h = st.number_input("cp caliente [kJ/kg·K]", 0.1, 20.0, 4.18)
        th_in = st.number_input("T entrada caliente [°C]", -50.0, 1500.0, 90.0)

        st.subheader("Fluido frío")
        m_c = st.number_input("ṁ frío [kg/s]", 0.01, 1e4, 1.5, format="%.3f")
        cp_c = st.number_input("cp frío [kJ/kg·K]", 0.1, 20.0, 4.18)
        tc_in = st.number_input("T entrada fría [°C]", -50.0, 1500.0, 20.0)

        st.subheader("Equipo")
        u = st.number_input("U global [kW/m²·K]", 0.001, 50.0, 0.8, format="%.3f")

    if modo.startswith("Dimensionamiento"):
        th_out = st.number_input("T salida caliente (objetivo) [°C]",
                                 -50.0, 1500.0, 60.0)
        _render_dimensionado(conf, m_h, cp_h, th_in, th_out,
                             m_c, cp_c, tc_in, u)
    else:
        area = st.number_input("Área disponible [m²]", 0.01, 1e5, 20.0)
        _render_simulacion(conf, m_h, cp_h, th_in, m_c, cp_c, tc_in, u, area)

    _grafica_efectividad(conf)

def _render_dimensionado(conf, m_h, cp_h, th_in, th_out,
                         m_c, cp_c, tc_in, u) -> None:
    try:
        r = hx.dimensionar(conf, m_h, cp_h, th_in, th_out,
                           m_c, cp_c, tc_in, u)
    except ValueError as exc:
        st.error(str(exc))
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Carga térmica Q", f"{r['q']:.2f} kW")
    c2.metric("T salida fría", f"{r['tc_out']:.2f} °C")
    c3.metric("ΔTml", f"{r['dtlm']:.2f} K")
    c4.metric("Factor F", f"{r['f']:.3f}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Área (LMTD)", f"{r['area_lmtd']:.2f} m²")
    c6.metric("Efectividad ε", f"{r['efectividad']:.3f}")
    c7.metric("NTU", f"{r['ntu']:.3f}")
    c8.metric("Área (ε-NTU)", f"{r['area_ntu']:.2f} m²")

    if r["advertencia"]:
        st.warning(r["advertencia"])

def _render_simulacion(conf, m_h, cp_h, th_in, m_c, cp_c, tc_in,
                       u, area) -> None:
    r = hx.simular(conf, m_h, cp_h, th_in, m_c, cp_c, tc_in, u, area)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Carga térmica Q", f"{r['q']:.2f} kW")
    c2.metric("T salida caliente", f"{r['th_out']:.2f} °C")
    c3.metric("T salida fría", f"{r['tc_out']:.2f} °C")
    c4.metric("Efectividad ε", f"{r['efectividad']:.3f}")

def _grafica_efectividad(conf: str) -> None:
    st.subheader("Curvas ε–NTU")
    ntu = np.linspace(0.0, 6.0, 200)
    fig = go.Figure()
    for cr in [0.0, 0.25, 0.5, 0.75, 1.0]:
        cr_eff = max(cr, 1e-6)
        eps = [hx.efectividad(n, cr_eff, conf) for n in ntu]
        fig.add_trace(go.Scatter(x=ntu, y=eps, mode="lines",
                                 name=f"Cr = {cr:g}"))
    fig.update_layout(
        xaxis_title="NTU",
        yaxis_title="Efectividad ε",
        yaxis_range=[0, 1],
        template="plotly_white",
        height=420,
        legend_title_text="Cmin/Cmax",
    )
    st.plotly_chart(fig, use_container_width=True)

    tabla = pd.DataFrame({"NTU": [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]})
    for cr in [0.25, 0.5, 1.0]:
        tabla[f"ε (Cr={cr:g})"] = [
            round(hx.efectividad(n, cr, conf), 4) for n in tabla["NTU"]
        ]
    with st.expander("Tabla de valores ε–NTU"):
        st.dataframe(tabla, hide_index=True, use_container_width=True)

# ----------------------------------------------------------------- Menú
MODULOS = {
    "Intercambiador de calor (LMTD / e-NTU)": render_intercambiador,
    "Diseno 3D y Balance": vista_3d.render,  
}

st.sidebar.title("⚗️ Operaciones Unitarias")
seleccion = st.sidebar.selectbox("Módulo", list(MODULOS))
st.sidebar.caption("Diseño y simulación de equipos · v0.2.0")

MODULOS[seleccion]()
