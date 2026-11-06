"""
Núcleo de cálculo para intercambiadores de calor.

Métodos implementados
----------------------
- LMTD (diferencia media logarítmica de temperatura) con factor de
  corrección F para carcasa y tubos 1-2.
- ε-NTU (efectividad - número de unidades de transferencia), directo e
  inverso, para seis configuraciones de flujo.

Capacidades térmicas (C = m·cp) en kW/K; área en m²; U en kW/(m²·K).

Referencias: Incropera et al., Fundamentals of Heat and Mass Transfer,
7.ª ed., cap. 11; Shah & Sekulic para flujo cruzado.
"""

from __future__ import annotations

import numpy as np

CONFIGURACIONES = {
    "contraflujo": "Contraflujo",
    "paralelo": "Flujo paralelo",
    "carcasa_tubos_1_2": "Carcasa y tubos 1-2",
    "cruzado_sin_mezclar": "Flujo cruzado, ambos sin mezclar",
    "cruzado_cmax_mezclado": "Flujo cruzado, Cmax mezclado",
    "cruzado_cmin_mezclado": "Flujo cruzado, Cmin mezclado",
}


# ------------------------------------------------------------------ LMTD
def lmtd(dt1: float, dt2: float) -> float:
    """Diferencia media logarítmica de temperatura [K]."""
    if dt1 <= 0 or dt2 <= 0:
        raise ValueError(
            "Cruce térmico: las diferencias de temperatura deben ser "
            "positivas en ambos extremos del intercambiador."
        )
    if abs(dt1 - dt2) < 1e-9:
        return dt1
    return (dt1 - dt2) / np.log(dt1 / dt2)


def factor_f_1_2(th_in: float, th_out: float,
                 tc_in: float, tc_out: float) -> float:
    """Factor de corrección F para intercambiador carcasa y tubos 1-2."""
    r = (th_in - th_out) / (tc_out - tc_in)      # razón de temperaturas R
    p = (tc_out - tc_in) / (th_in - tc_in)       # eficiencia térmica P
    if p <= 0 or p >= 1:
        raise ValueError("Eficiencia térmica P fuera de rango (0 < P < 1).")
    if abs(r - 1.0) < 1e-9:
        r = 1.0 + 1e-9
    s = np.sqrt(r ** 2 + 1.0)
    numerador = (s / (r - 1.0)) * np.log((1.0 - p) / (1.0 - p * r))
    denominador = np.log(
        (2.0 / p - 1.0 - r + s) / (2.0 / p - 1.0 - r - s)
    )
    return numerador / denominador


# ----------------------------------------------------------------- ε-NTU
def efectividad(ntu: float, cr: float, conf: str) -> float:
    """Efectividad ε a partir de NTU y Cr = Cmin/Cmax."""
    if conf == "contraflujo":
        if abs(cr - 1.0) < 1e-9:
            return ntu / (1.0 + ntu)
        e = np.exp(-ntu * (1.0 - cr))
        return (1.0 - e) / (1.0 - cr * e)
    if conf == "paralelo":
        return (1.0 - np.exp(-ntu * (1.0 + cr))) / (1.0 + cr)
    if conf == "carcasa_tubos_1_2":
        s = np.sqrt(1.0 + cr ** 2)
        e = np.exp(-ntu * s)
        return 2.0 / (1.0 + cr + s * (1.0 + e) / (1.0 - e))
    if conf == "cruzado_sin_mezclar":
        return 1.0 - np.exp(
            (np.exp(-cr * ntu ** 0.78) - 1.0) / (cr * ntu ** -0.22)
        )
    if conf == "cruzado_cmax_mezclado":
        return (1.0 - np.exp(-cr * (1.0 - np.exp(-ntu)))) / cr
    if conf == "cruzado_cmin_mezclado":
        return 1.0 - np.exp(-(1.0 - np.exp(-cr * ntu)) / cr)
    raise ValueError(f"Configuración desconocida: {conf}")


def ntu_desde_efectividad(eps: float, cr: float, conf: str) -> float:
    """NTU a partir de la efectividad (relaciones inversas).

    Flujo cruzado sin mezclar no tiene forma cerrada: bisección.
    """
    if not 0 < eps < 1:
        raise ValueError("La efectividad debe estar entre 0 y 1.")
    if conf == "contraflujo":
        if abs(cr - 1.0) < 1e-9:
            return eps / (1.0 - eps)
        return np.log((1.0 - eps * cr) / (1.0 - eps)) / (1.0 - cr)
    if conf == "paralelo":
        return -np.log(1.0 - eps * (1.0 + cr)) / (1.0 + cr)
    if conf == "carcasa_tubos_1_2":
        s = np.sqrt(1.0 + cr ** 2)
        e_rel = (2.0 / eps - (1.0 + cr)) / s
        if e_rel <= 1.0:
            raise ValueError(
                "Efectividad inalcanzable para esta configuración y Cr."
            )
        return -np.log((e_rel - 1.0) / (e_rel + 1.0)) / s
    if conf == "cruzado_cmax_mezclado":
        return -np.log(1.0 + np.log(1.0 - eps * cr) / cr)
    if conf == "cruzado_cmin_mezclado":
        return -np.log(cr * np.log(1.0 - eps) + 1.0) / cr
    if conf == "cruzado_sin_mezclar":
        lo, hi = 1e-9, 100.0
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if efectividad(mid, cr, conf) < eps:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)
    raise ValueError(f"Configuración desconocida: {conf}")


# ------------------------------------------------------ Flujos de trabajo
def capacidades(m_h: float, cp_h: float,
                m_c: float, cp_c: float) -> tuple[float, float]:
    """Capacidades térmicas Ch y Cc en kW/K (m en kg/s, cp en kJ/kg·K)."""
    return m_h * cp_h, m_c * cp_c


def dimensionar(
    conf: str,
    m_h: float, cp_h: float, th_in: float, th_out: float,
    m_c: float, cp_c: float, tc_in: float,
    u: float,
) -> dict:
    """Dimensiona el área para un servicio dado (LMTD y ε-NTU)."""
    ch, cc = capacidades(m_h, cp_h, m_c, cp_c)
    q = ch * (th_in - th_out)
    tc_out = tc_in + q / cc
    cmin, cmax = min(ch, cc), max(ch, cc)
    cr = cmin / cmax

    dt1 = th_in - tc_out if conf != "paralelo" else th_in - tc_in
    dt2 = th_out - tc_in if conf != "paralelo" else th_out - tc_out
    dtlm = lmtd(dt1, dt2)

    f = 1.0
    advertencia = None
    if conf == "carcasa_tubos_1_2":
        f = factor_f_1_2(th_in, th_out, tc_in, tc_out)
        if f < 0.75:
            advertencia = (
                f"F = {f:.3f} < 0.75: diseño no recomendable; considera "
                "varios pasos por carcasa."
            )

    area_lmtd = q / (u * f * dtlm)

    eps = q / (cmin * (th_in - tc_in))
    ntu = ntu_desde_efectividad(eps, cr, conf)
    area_ntu = ntu * cmin / u

    return {
        "q": q, "tc_out": tc_out, "ch": ch, "cc": cc,
        "cmin": cmin, "cr": cr, "dtlm": dtlm, "f": f,
        "area_lmtd": area_lmtd, "efectividad": eps, "ntu": ntu,
        "area_ntu": area_ntu, "advertencia": advertencia,
    }


def simular(
    conf: str,
    m_h: float, cp_h: float, th_in: float,
    m_c: float, cp_c: float, tc_in: float,
    u: float, area: float,
) -> dict:
    """Simulación (rating): con área conocida, calcula Q y salidas."""
    ch, cc = capacidades(m_h, cp_h, m_c, cp_c)
    cmin, cmax = min(ch, cc), max(ch, cc)
    cr = cmin / cmax
    ntu = u * area / cmin
    eps = efectividad(ntu, cr, conf)
    q = eps * cmin * (th_in - tc_in)
    th_out = th_in - q / ch
    tc_out = tc_in + q / cc
    return {
        "q": q, "th_out": th_out, "tc_out": tc_out,
        "efectividad": eps, "ntu": ntu, "cr": cr,
    }
