"""Motore di calcolo del calcolatore: legge calcolatore_modelli.json e calcola il rischio. Stessa formula del passo 34 (Python) e di calcolatore.js."""
from __future__ import annotations

import json
import math
from pathlib import Path

PERCORSO = Path(__file__).with_name("calcolatore_modelli.json")


def carica(percorso: Path = PERCORSO) -> dict:
    return json.loads(Path(percorso).read_text(encoding="utf-8"))


def rischio(modello: dict, valori: dict) -> float:
    """Fine-Gray: 1 - exp(-H0 * exp(lp - c)), lp = somma coef * (x - media). Logistico: 1 / (1 + exp(-(intercetta + somma coef * x)))."""
    if modello["tipo"] == "logistico":
        z = modello["intercetta"] + sum(v["coef"] * float(valori[v["nome"]]) for v in modello["variabili"])
        return 1.0 / (1.0 + math.exp(-z))
    lp = sum(v["coef"] * (float(valori[v["nome"]]) - v["media"]) for v in modello["variabili"])
    b = modello["baseline"]
    return 1.0 - math.exp(-b["H0"] * math.exp(lp - b["c"]))


def _presente(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def candidati(doc: dict, esito: str, anni: int) -> list:
    """Modelli di un esito e di un orizzonte, dal piu' ricco al piu' semplice."""
    m = [x for x in doc["modelli"] if x["esito"] == esito and x["orizzonte_anni"] == anni]
    return sorted(m, key=lambda x: (-len(x["variabili"]), x["modello"] != "lab"))


def scegli(doc: dict, esito: str, anni: int, valori: dict, preferenza: str = "automatico"):
    """Modello da usare: con preferenza 'nucleo' o 'lab' solo quello, se tutti i suoi ingressi sono presenti; 'automatico' il piu' ricco completo."""
    for m in candidati(doc, esito, anni):
        if preferenza != "automatico" and m["modello"] != preferenza:
            continue
        if all(_presente(valori.get(v["nome"])) for v in m["variabili"]):
            return m
    return None


def avvisi(doc: dict, modello: dict, valori: dict) -> list:
    out = []
    for v in modello["variabili"]:
        r = doc["ingressi"].get(v["nome"])
        x = valori.get(v["nome"])
        if r and _presente(x) and (float(x) < r["p1"] or float(x) > r["p99"]):
            out.append(f"{r['etichetta']}: {x} fuori dall'intervallo abituale della coorte ({r['p1']:.4g}-{r['p99']:.4g})")
    return out


# ---- calcolo di piu' esiti insieme (usato dall'app) ----
DEBOLI = {"tod", "composito_nonfatale", "ascvd"}
POPOLAZIONI = {
    "dcsi_progressione": "Il DCSI all'indice è 0",
    "ascvd": "Il paziente non ha ASCVD pregressa",
    "composito_nonfatale": "Il paziente non ha ASCVD pregressa",
}
BREVI = {
    "morte_surrogata": "Mortalità", "dcsi_progressione": "Progr. DCSI", "oculistica_inc": "Compl. oculare",
    "incremento_dcsi2": "DCSI +2", "hba1c_fuori_target": "HbA1c fuori target", "tt_fuori_target": "TT <70%",
    "tt_fuori_target_tol365": "TT <70% (tol. 365, esplor.)", "tod": "TOD", "composito_nonfatale": "Comp. non fatale", "ascvd": "ASCVD",
}
ORDINE = ["morte_surrogata", "dcsi_progressione", "oculistica_inc", "incremento_dcsi2", "hba1c_fuori_target",
          "tt_fuori_target", "tt_fuori_target_tol365", "tod", "composito_nonfatale", "ascvd"]
PREDEFINITI = {"morte_surrogata", "dcsi_progressione", "oculistica_inc", "incremento_dcsi2", "hba1c_fuori_target", "tt_fuori_target"}
DERIVATI = {"P", "n_principi_attivi"}


def elenco_esiti(doc: dict) -> list:
    """Esiti disponibili, in ordine fisso: chiave, etichetta, orizzonti, flag debole/esplorativo."""
    out = []
    for e in ORDINE:
        ms = [m for m in doc["modelli"] if m["esito"] == e]
        if not ms:
            continue
        etichetta = ms[0]["etichetta"].split(" a ")[0] if e == "hba1c_fuori_target" else ms[0]["etichetta"]
        out.append({"chiave": e, "etichetta": etichetta, "breve": BREVI.get(e, e), "anni": sorted({m["orizzonte_anni"] for m in ms}),
                    "debole": e in DEBOLI, "esplorativo": ms[0].get("stato") == "esplorativo", "requisiti": ms[0].get("requisiti", "")})
    return out


def anni_effettivi(doc: dict, esito: str, anni: int):
    """Orizzonte usato: quello scelto se esiste, l'unico disponibile se fisso (tempo in target), altrimenti None."""
    disp = sorted({m["orizzonte_anni"] for m in doc["modelli"] if m["esito"] == esito})
    if anni in disp:
        return anni
    return disp[0] if len(disp) == 1 else None


def ingressi_richiesti(doc: dict, esito: str, anni: int, preferenza: str = "automatico"):
    """(obbligatori, facoltativi): obbligatori = ingressi del modello nucleo (o lab se scelto), facoltativi = esami che aggiungono il modello lab."""
    a = anni_effettivi(doc, esito, anni)
    cand = candidati(doc, esito, a) if a else []
    nucleo = [v["nome"] for m in cand if m["modello"] == "nucleo" for v in m["variabili"]]
    lab = [v["nome"] for m in cand if m["modello"] == "lab" for v in m["variabili"]]
    if preferenza == "lab":
        return list(dict.fromkeys(lab)), []
    ob = list(dict.fromkeys(nucleo or lab))
    return ob, ([x for x in dict.fromkeys(lab) if x not in ob] if preferenza == "automatico" else [])


def calcola(doc: dict, esito: str, anni: int, valori: dict, preferenza: str = "automatico", popolazione_ok: bool = True) -> dict:
    """Risultato di un esito: stato 'ok', 'mancano' (con elenco), 'popolazione' o 'non_disponibile'."""
    a = anni_effettivi(doc, esito, anni)
    r = {"esito": esito, "anni": a, "stato": "ok", "rischio": None, "modello": None, "mancanti": [], "avvisi": []}
    if a is None:
        r["stato"] = "non_disponibile"
        return r
    cand = [m for m in candidati(doc, esito, a) if preferenza == "automatico" or m["modello"] == preferenza]
    if not popolazione_ok:
        r["stato"] = "popolazione"
        return r
    m = scegli(doc, esito, a, valori, preferenza)
    if m is None:
        mancanti = min(([v["nome"] for v in c["variabili"] if not _presente(valori.get(v["nome"]))] for c in cand), key=len, default=[])
        r["stato"], r["mancanti"] = "mancano", mancanti
        return r
    r.update(modello=m, rischio=rischio(m, valori), avvisi=avvisi(doc, m, valori))
    return r
