import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import potenze


def test_valori_noti_della_tabella():
    assert potenze.potenza("METFORMINA", 999) == 7 and potenze.potenza("METFORMINA", 1000) == 9
    assert potenze.potenza("METFORMINA", 1500) == 12 and potenze.potenza("METFORMINA", 2000) == 13
    assert potenze.potenza("DAPAGLIFLOZIN", 5) == 9 and potenze.potenza("DAPAGLIFLOZIN", 10) == 11
    assert potenze.potenza("LIRAGLUTIDE", 1.8) == 13 and potenze.potenza("LIRAGLUTIDE", 1.2) == 10
    assert potenze.potenza("SEMAGLUTIDE SC", 1) == 17 and potenze.potenza("SEMAGLUTIDE SC", 0.5) == 16
    assert potenze.potenza("TIRZEPATIDE", 15) == 25 and potenze.potenza("INSULINA GLARGINE", None) == 17


def test_terapia_somma_e_mancanti():
    assert potenze.terapia({"METFORMINA": 1700, "SITAGLIPTIN": None}) == (19, 2, [])
    p, n, manc = potenze.terapia({"METFORMINA": None, "SITAGLIPTIN": None})
    assert p is None and n == 2 and manc == ["METFORMINA"]
    assert potenze.terapia({})[0] is None


def test_identica_a_mi_drugs_se_disponibile():
    drugs = pytest.importorskip("mi.drugs")
    for pa in list(potenze.TABELLA["dose_dipendenti"]) + list(potenze.TABELLA["fisse"]):
        for dose in [0.1, 0.5, 1, 1.5, 1.8, 2, 3, 4.5, 5, 6, 9, 10, 13, 14, 15, 24, 25, 299, 300, 999, 1000, 1499, 1500, 1999, 2000, 3000]:
            assert potenze.potenza(pa, dose) == drugs.potenza(pa, dose), (pa, dose)
