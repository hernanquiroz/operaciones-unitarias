"""Pruebas del núcleo de intercambiadores: consistencia LMTD/ε-NTU."""

import numpy as np
import pytest

from modulos import intercambiador as hx

CONF_TODAS = list(hx.CONFIGURACIONES)

def test_lmtd_simetrico():
    assert hx.lmtd(50.0, 50.0) == pytest.approx(50.0)

def test_lmtd_cruce_termico():
    with pytest.raises(ValueError):
        hx.lmtd(40.0, -5.0)

@pytest.mark.parametrize("conf", CONF_TODAS)
@pytest.mark.parametrize("cr", [0.25, 0.5, 0.75, 0.95])
def test_efectividad_roundtrip(conf, cr):
    """efectividad -> NTU -> efectividad debe ser consistente."""
    for ntu in [0.2, 0.8, 1.5, 3.0]:
        eps = hx.efectividad(ntu, cr, conf)
        ntu2 = hx.ntu_desde_efectividad(eps, cr, conf)
        assert ntu2 == pytest.approx(ntu, rel=1e-6)

def test_efectividad_contraflujo_cr1():
    assert hx.efectividad(2.0, 1.0, "contraflujo") == pytest.approx(2.0 / 3.0)

def test_dimensionar_consistencia_lmtd_ntu():
    """El área por LMTD y por ε-NTU debe coincidir (contraflujo, F = 1)."""
    r = hx.dimensionar(
        conf="contraflujo",
        m_h=2.0, cp_h=4.18, th_in=90.0, th_out=60.0,
        m_c=1.5, cp_c=4.18, tc_in=20.0,
        u=0.8,
    )
    assert r["area_ntu"] == pytest.approx(r["area_lmtd"], rel=1e-6)

def test_simular_inversa_de_dimensionar():
    """Simular con el área dimensionada debe devolver las mismas salidas."""
    d = hx.dimensionar(
        conf="contraflujo",
        m_h=2.0, cp_h=4.18, th_in=90.0, th_out=60.0,
        m_c=1.5, cp_c=4.18, tc_in=20.0,
        u=0.8,
    )
    s = hx.simular(
        conf="contraflujo",
        m_h=2.0, cp_h=4.18, th_in=90.0,
        m_c=1.5, cp_c=4.18, tc_in=20.0,
        u=0.8, area=d["area_lmtd"],
    )
    assert s["q"] == pytest.approx(d["q"], rel=1e-6)
    assert s["th_out"] == pytest.approx(60.0, abs=1e-3)
    assert s["tc_out"] == pytest.approx(d["tc_out"], rel=1e-6)

def test_simular_cruzado_sin_mezclar():
    r = hx.simular(
        conf="cruzado_sin_mezclar",
        m_h=1.0, cp_h=2.0, th_in=120.0,
        m_c=2.0, cp_c=1.0, tc_in=25.0,
        u=0.5, area=10.0,
    )
    # Ch = 2.0, Cc = 2.0 -> Cr = 1, NTU = 2.5
    assert r["ntu"] == pytest.approx(2.5)
    assert 0 < r["efectividad"] < 1
