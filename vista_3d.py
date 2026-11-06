"""Vista 3D del intercambiador: modelo del equipo + superficies + balance."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import nucleo_hx as hx


def render():
    st.header("Diseño 3D y Balance de Masa y Energía")

    # --- Sidebar: mismos datos del intercambiador ---
    with st.sidebar:
        st.subheader("Fluido caliente")
        m_h = st.number_input("m caliente [kg/s]", 0.01, 1e4, 2.0, format="%.3f")
        cp_h = st.number_input("cp caliente [kJ/kg*K]", 0.1, 20.0, 4.18)
        th_in = st.number_input("T entrada caliente [C]", -50.0, 1500.0, 90.0)

        st.subheader("Fluido frio")
        m_c = st.number_input("m frio [kg/s]", 0.01, 1e4, 1.5, format="%.3f")
        cp_c = st.number_input("cp frio [kJ/kg*K]", 0.1, 20.0, 4.18)
        tc_in = st.number_input("T entrada fria [C]", -50.0, 1500.0, 20.0)

        st.subheader("Equipo")
        u = st.number_input("U global [kW/m2*K]", 0.001, 50.0, 0.8, format="%.3f")
        area = st.number_input("Area [m2]", 0.01, 1e5, 20.0)

    # --- Calcular ---
    try:
        r = hx.simular("contraflujo", m_h, cp_h, th_in, m_c, cp_c, tc_in, u, area)
    except ValueError as exc:
        st.error(str(exc))
        return

    # --- Metricas del balance ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Q transferido", f"{r['q']:.2f} kW")
    c2.metric("T salida caliente", f"{r['th_out']:.2f} C")
    c3.metric("T salida fria", f"{r['tc_out']:.2f} C")
    c4.metric("Efectividad", f"{r['efectividad']:.3f}")

    # --- Tabla de balance ---
    st.subheader("Balance de masa y energia")
    st.dataframe(
        pd.DataFrame(
            [
                ["Entrada caliente", m_h, cp_h, th_in, m_h * cp_h * th_in],
                ["Salida caliente", m_h, cp_h, r["th_out"], m_h * cp_h * r["th_out"]],
                ["Entrada fria", m_c, cp_c, tc_in, m_c * cp_c * tc_in],
                ["Salida fria", m_c, cp_c, r["tc_out"], m_c * cp_c * r["tc_out"]],
            ],
            columns=["Corriente", "m [kg/s]", "cp [kJ/kg*K]", "T [C]", "H [kW]"],
        ),
        hide_index=True,
        use_container_width=True
    )
    dh = m_h * cp_h * (th_in - r["th_out"]) - m_c * cp_c * (r["tc_out"] - tc_in)
    st.info(f"Balance de energia: Q cedido - Q ganado = {dh:.6f} kW (cero = balance cerrado)")

    # --- Tabs 3D ---
    tab1, tab2, tab3 = st.tabs(
        ["Modelo 3D del equipo", "Superficie epsilon-NTU", "Perfil de temperaturas"]
    )

    with tab1:
        _mostrar_modelo_3d(r, m_h, cp_h, m_c, cp_c, th_in, tc_in)

    with tab2:
        _mostrar_superficie_3d()

    with tab3:
        _mostrar_perfil_3d(th_in, r["th_out"], tc_in, r["tc_out"])


# ------------------------------------------------------------------ Modelo 3D
def _mostrar_modelo_3d(r, m_h, cp_h, m_c, cp_c, th_in, tc_in):
    n = 30
    theta = np.linspace(0, 2 * np.pi, n)
    z = np.linspace(0, 1, n)
    T, Z = np.meshgrid(theta, z)

    # Carcasa
    X = 0.25 * np.cos(T)
    Y = 0.25 * np.sin(T)
    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z, colorscale=[[0, "#B0BEC5"], [1, "#B0BEC5"]],
        opacity=0.35, showscale=False, name="Carcasa",
    ))

    # Tubos interiores
    for pos in [(-0.08, -0.08), (-0.08, 0.08), (0.08, -0.08), (0.08, 0.08)]:
        x_t = pos[0] + 0.03 * np.cos(T)
        y_t = pos[1] + 0.03 * np.sin(T)
        fig.add_trace(go.Surface(
            x=x_t, y=y_t, z=Z, colorscale=[[0, "#78909C"], [1, "#78909C"]],
            opacity=0.85, showscale=False, name="Tubos",
        ))

    # Flechas de flujo caliente (rojo, z=1 -> z=0)
    fig.add_trace(go.Cone(
        x=[0], y=[0], z=[0.85], u=[0], v=[0], w=[-0.3],
        colorscale=[[0, "#D32F2F"], [1, "#D32F2F"]], showscale=False,
        sizemode="absolute", sizeref=0.15, name="Caliente",
    ))
    # Flechas de flujo frio (azul, z=0 -> z=1)
    fig.add_trace(go.Cone(
        x=[0.35], y=[0], z=[0.15], u=[0], v=[0], w=[0.3],
        colorscale=[[0, "#1565C0"], [1, "#1565C0"]], showscale=False,
        sizemode="absolute", sizeref=0.15, name="Frio",
    ))

    # Etiquetas de temperatura
    fig.add_trace(go.Scatter3d(
        x=[0.4, 0.4, -0.4, -0.4],
        y=[0, 0, 0, 0],
        z=[1.1, -0.1, 1.1, -0.1],
        mode="text",
        text=[
            f"Frio entra {tc_in:.1f} C",
            f"Frio sale {r['tc_out']:.1f} C",
            f"Caliente entra {th_in:.1f} C",
            f"Caliente sale {r['th_out']:.1f} C",
        ],
        textfont=dict(size=11, color="#333333"),
        showlegend=False,
    ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0),
        height=520,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------------------- Superficie 3D
def _mostrar_superficie_3d():
    ntu = np.linspace(0.01, 5.0, 60)
    cr = np.linspace(0.0, 1.0, 60)
    N, C = np.meshgrid(ntu, cr)
    E = np.zeros_like(N)
    for i in range(len(cr)):
        for j in range(len(ntu)):
            E[i, j] = hx.efectividad(N[i, j], max(C[i, j], 1e-6), "contraflujo")

    fig = go.Figure(data=[go.Surface(
        x=N, y=C, z=E,
        colorscale="Viridis",
        colorbar=dict(title="epsilon"),
        opacity=0.92,
    )])
    fig.update_layout(
        scene=dict(
            xaxis_title="NTU",
            yaxis_title="Cr",
            zaxis_title="epsilon",
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0),
        height=520,
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------- Perfil 3D
def _mostrar_perfil_3d(th_in, th_out, tc_in, tc_out):
    x = np.linspace(0, 1, 50)
    y = np.linspace(0, 1, 20)
    X, Y = np.meshgrid(x, y)
    Z_h = th_out + (th_in - th_out) * (1 - X)
    Z_c = tc_in + (tc_out - tc_in) * (1 - X)

    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z_h,
        colorscale=[[0, "#FFCDD2"], [1, "#B71C1C"]],
        opacity=0.85, showscale=False, name="Caliente",
    ))
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z_c,
        colorscale=[[0, "#BBDEFB"], [1, "#0D47A1"]],
        opacity=0.85, showscale=False, name="Frio",
    ))
    fig.update_layout(
        scene=dict(
            xaxis_title="Posicion",
            yaxis_title="",
            zaxis_title="T [C]",
            yaxis=dict(showticklabels=False),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0),
        height=520,
    )
    st.plotly_chart(fig, use_container_width=True)
