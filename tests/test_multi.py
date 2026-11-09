import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import motore

DOC = motore.carica()
BASE = {"eta_indice": 68, "sesso_M": 1, "TOD_ER_max": 1, "hba1c_basale": 58, "durata_dm": 10, "P": 19, "n_principi_attivi": 2, "dcsi_basale": 0}


def test_calcola_ok_mancano_e_non_disponibile():
    r = motore.calcola(DOC, "morte_surrogata", 5, BASE)
    assert r["stato"] == "ok" and 0 < r["rischio"] < 1 and r["modello"]["modello"] == "nucleo"
    r = motore.calcola(DOC, "morte_surrogata", 5, {**BASE, "lab_egfr": 70})
    assert r["modello"]["modello"] == "lab"
    r = motore.calcola(DOC, "oculistica_inc", 5, {"eta_indice": 60})
    assert r["stato"] == "mancano" and set(r["mancanti"]) == {"durata_dm", "hba1c_basale"}
    assert motore.calcola(DOC, "hba1c_fuori_target", 10, BASE)["stato"] == "non_disponibile"
    assert motore.calcola(DOC, "tt_fuori_target", 10, BASE)["anni"] == 3
    assert motore.calcola(DOC, "ascvd", 5, BASE, popolazione_ok=False)["stato"] == "popolazione"


def test_ingressi_richiesti():
    ob, fac = motore.ingressi_richiesti(DOC, "morte_surrogata", 5)
    assert ob == ["eta_indice", "sesso_M", "TOD_ER_max"] and fac == ["lab_egfr"]
    assert motore.ingressi_richiesti(DOC, "morte_surrogata", 5, "lab")[1] == []
    assert motore.ingressi_richiesti(DOC, "hba1c_fuori_target", 10) == ([], [])


def test_elenco_esiti():
    e = motore.elenco_esiti(DOC)
    assert [x["chiave"] for x in e][:2] == ["morte_surrogata", "dcsi_progressione"] and len(e) == 10
    assert next(x for x in e if x["chiave"] == "tod")["debole"]


def test_app_multi_esito_calcola_e_disegna_il_radar():
    import pytest
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=60)
    assert not at.exception
    at.number_input(key="eta_indice").set_value(68)
    at.selectbox(key="sesso_M").set_value("Maschio")
    at.number_input(key="hba1c_basale").set_value(58)
    at.number_input(key="durata_dm").set_value(10)
    at.checkbox(key="nessuna_comp").check()
    at.multiselect(key="principi_attivi").set_value(["METFORMINA", "SITAGLIPTIN"])
    at.run(timeout=60)
    at.number_input(key="dose_METFORMINA").set_value(1700)
    at.run(timeout=60)
    at.button[-1].click().run(timeout=60)
    assert not at.exception
    assert len(at.dataframe) == 1 and len(at.dataframe[0].value) == 6
    assert not any("non calcolato" in str(x) for x in at.dataframe[0].value["Rischio"])
