"""Inserimento guidato di TOD e DCSI all'indice dalle complicanze documentate.
TOD_ER_max = massimo di TOD_ER tra le voci scelte (0 se nessuna); DCSI = somma, sui 7 domini, del punteggio massimo tra le voci scelte.
Tabelle: complicanze.json, da Marcellini_Index_Allegati_v2.xlsx (nessun dato di pazienti)."""
from __future__ import annotations

import json
from pathlib import Path

TABELLA = json.loads(Path(__file__).with_name("complicanze.json").read_text(encoding="utf-8"))
DOMINI = TABELLA["domini_dcsi"]
_VOCI = {(v["macroarea"], v["voce"]): v for v in TABELLA["voci"]}


def distretti() -> list:
    return list(dict.fromkeys(v["macroarea"] for v in TABELLA["voci"]))


def voci_di(distretto: str) -> list:
    return [v["voce"] for v in TABELLA["voci"] if v["macroarea"] == distretto]


def calcola(scelte: list) -> dict:
    """scelte: elenco di (distretto, voce). Restituisce TOD_ER_max, dcsi_basale, punteggio per dominio e ASCVD pregressa (0/1)."""
    per_dominio = {d: 0.0 for d in DOMINI}
    tod, asc = 0, 0
    for k in scelte:
        v = _VOCI[tuple(k)]
        tod, asc = max(tod, v["tod_er"]), max(asc, v["ascvd"])
        for d, p in v["dcsi"].items():
            per_dominio[d] = max(per_dominio[d], p)
    return {"TOD_ER_max": tod, "dcsi_basale": sum(per_dominio.values()), "per_dominio": per_dominio, "ascvd": asc}
