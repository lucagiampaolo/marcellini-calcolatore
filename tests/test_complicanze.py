import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import complicanze


def _voce(distretto, **cond):
    return next(v for v in complicanze.TABELLA["voci"] if v["macroarea"] == distretto and all(v[k] == x for k, x in cond.items()))


def test_nessuna_complicanza_e_massimo_per_dominio():
    r = complicanze.calcola([])
    assert r["TOD_ER_max"] == 0 and r["dcsi_basale"] == 0 and r["ascvd"] == 0
    a = next(v for v in complicanze.TABELLA["voci"] if v["macroarea"] == "Occhio" and v["dcsi"].get("OCULISTICA") == 1)
    b = next(v for v in complicanze.TABELLA["voci"] if v["macroarea"] == "Occhio" and v["dcsi"].get("OCULISTICA") == 2)
    assert complicanze.calcola([("Occhio", a["voce"])])["dcsi_basale"] == 1
    assert complicanze.calcola([("Occhio", a["voce"]), ("Occhio", b["voce"])])["dcsi_basale"] == 2   # massimo nel dominio, non somma
    assert complicanze.calcola([("Occhio", b["voce"])])["TOD_ER_max"] == b["tod_er"]


def test_somma_tra_domini_e_ascvd():
    occ = next(v for v in complicanze.TABELLA["voci"] if v["macroarea"] == "Occhio" and v["dcsi"].get("OCULISTICA") == 1)
    ren = next(v for v in complicanze.TABELLA["voci"] if v["macroarea"] == "Rene" and v["dcsi"].get("NEFROPATIA") == 1)
    r = complicanze.calcola([("Occhio", occ["voce"]), ("Rene", ren["voce"])])
    assert r["dcsi_basale"] == 2 and r["per_dominio"]["NEFROPATIA"] == 1
    asc = next(v for v in complicanze.TABELLA["voci"] if v["ascvd"] == 1)
    assert complicanze.calcola([(asc["macroarea"], asc["voce"])])["ascvd"] == 1


def test_app_guidata_senza_conoscere_i_punti():
    import pytest
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=60)
    assert not at.exception
    assert not any(n.key in ("TOD_ER_max", "dcsi_basale") for n in at.number_input)
    occ = next(v for v in complicanze.TABELLA["voci"] if v["macroarea"] == "Occhio" and v["dcsi"].get("OCULISTICA") == 2)
    at.multiselect(key="comp_Occhio").set_value([occ["voce"]])
    at.run(timeout=60)
    assert any("DCSI: **2**" in m.value for m in at.markdown), [m.value for m in at.markdown]
    assert any("Non vale per questo paziente" in m.value for m in at.markdown)
