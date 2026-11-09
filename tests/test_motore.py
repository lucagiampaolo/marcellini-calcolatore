import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import motore

DOC = motore.carica()


def _valori(m, x=60.0):
    return {v["nome"]: (1.0 if v["nome"] == "sesso_M" else x) for v in m["variabili"]}


def test_cinquanta_modelli_e_nessun_minimo_massimo():
    assert len(DOC["modelli"]) == 50
    assert all("min" not in r and "max" not in r for r in DOC["ingressi"].values())


def test_rischi_in_0_1_e_monotoni_con_l_eta_nella_mortalita():
    for m in DOC["modelli"]:
        assert 0 <= motore.rischio(m, _valori(m)) <= 1
    m = motore.scegli(DOC, "morte_surrogata", 5, {"eta_indice": 60, "sesso_M": 1, "TOD_ER_max": 0, "lab_egfr": 80}, "nucleo")
    r60 = motore.rischio(m, {"eta_indice": 60, "sesso_M": 1, "TOD_ER_max": 0})
    r80 = motore.rischio(m, {"eta_indice": 80, "sesso_M": 1, "TOD_ER_max": 0})
    assert r80 > r60


def test_formula_logistica_a_mano():
    m = next(x for x in DOC["modelli"] if x["tipo"] == "logistico")
    v = _valori(m, 50.0)
    z = m["intercetta"] + sum(c["coef"] * 50.0 if c["nome"] != "sesso_M" else c["coef"] for c in m["variabili"])
    assert math.isclose(motore.rischio(m, v), 1 / (1 + math.exp(-z)), rel_tol=1e-12)


def test_scegli_automatico_prende_il_lab_se_completo_altrimenti_nucleo():
    base = {"eta_indice": 65, "sesso_M": 1, "TOD_ER_max": 1}
    assert motore.scegli(DOC, "morte_surrogata", 5, base)["modello"] == "nucleo"
    assert motore.scegli(DOC, "morte_surrogata", 5, {**base, "lab_egfr": 70})["modello"] == "lab"
    assert motore.scegli(DOC, "morte_surrogata", 5, {"eta_indice": 65}, "lab") is None


def test_app_si_avvia_e_mostra_disclaimer():
    at = pytest_apptest()
    assert not at.exception
    assert any("sola ricerca" in w.value.lower() for w in at.warning)


def pytest_apptest():
    import pytest
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
