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
