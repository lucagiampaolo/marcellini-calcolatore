"""Potenza della terapia (P) e numero di principi attivi, dalla tabella delle potenze del Marcellini Index (potenze.json, copia di mi/potenze.yaml).
P = somma delle potenze dei principi attivi alla data indice; le combinazioni precostituite si scompongono nei principi attivi."""
from __future__ import annotations

import json
import math
from pathlib import Path

TABELLA = json.loads(Path(__file__).with_name("potenze.json").read_text(encoding="utf-8"))


def principi_attivi() -> dict:
    """Nome tecnico -> {'etichetta', 'unita' (None se potenza fissa)}."""
    out = {k: {"etichetta": v["etichetta"], "unita": v["unita"]} for k, v in TABELLA["dose_dipendenti"].items()}
    out.update({k: {"etichetta": v["etichetta"], "unita": None} for k, v in TABELLA["fisse"].items()})
    return dict(sorted(out.items(), key=lambda kv: kv[1]["etichetta"]))


def potenza(pa: str, dose: float | None):
    """Potenza del principio attivo alla dose giornaliera (o settimanale, per semaglutide sottocute, dulaglutide, tirzepatide); None se non calcolabile."""
    if pa in TABELLA["fisse"]:
        return TABELLA["fisse"][pa]["potenza"]
    t = TABELLA["dose_dipendenti"].get(pa)
    if t is None or dose is None or isinstance(dose, float) and math.isnan(dose) or not dose > 0:
        return None
    dose = round(float(dose), 6)
    for f in t["fasce"]:
        lim = f["fino_a"]
        if lim is None or dose < lim or (f["incluso"] and math.isclose(dose, lim, abs_tol=1e-9)):
            return f["potenza"]
    return t["fasce"][-1]["potenza"]


def terapia(scelte: dict):
    """scelte: {principio attivo: dose o None}. Restituisce (P, n. principi attivi, elenco dei principi attivi senza potenza calcolabile)."""
    pot, mancanti = 0, []
    for pa, dose in scelte.items():
        p = potenza(pa, dose)
        if p is None:
            mancanti.append(pa)
        else:
            pot += p
    return (None if mancanti or not scelte else pot), len(scelte), mancanti
