"""Calcolatore di rischio Marcellini Index (solo ricerca), multi-esito con radar. Avvio: streamlit run app.py"""
import plotly.graph_objects as go
import streamlit as st

import motore
import potenze

st.set_page_config(page_title="Marcellini Index - calcolatore di ricerca", layout="centered")
doc = motore.carica()
esiti = motore.elenco_esiti(doc)

st.title("Calcolatore di rischio - Marcellini Index")
st.warning(doc["disclaimer"] + " Non inserire dati identificativi.")

# ---- 1. esiti da calcolare ----
for e in esiti:
    st.session_state.setdefault("e_" + e["chiave"], e["chiave"] in motore.PREDEFINITI)


def _imposta(f):
    for e in esiti:
        st.session_state["e_" + e["chiave"]] = f(e)


st.subheader("1. Esiti da calcolare")
c1, c2, c3 = st.columns(3)
c1.button("Tutti", on_click=_imposta, args=(lambda e: True,), width="stretch")
c2.button("Nessuno", on_click=_imposta, args=(lambda e: False,), width="stretch")
c3.button("Solo AUC ≥ 0,65", on_click=_imposta, args=(lambda e: not e["debole"],), width="stretch")
col = st.columns(2)
for i, e in enumerate(esiti):
    sfx = (" · AUC debole" if e["debole"] else "") + (" · esplorativo" if e["esplorativo"] else "")
    col[i % 2].checkbox(e["etichetta"] + sfx, key="e_" + e["chiave"])
scelti = [e for e in esiti if st.session_state["e_" + e["chiave"]]]

o1, o2 = st.columns(2)
anni = o1.radio("Orizzonte (anni)", [3, 5, 10], index=1, horizontal=True, help="Tempo in target ha orizzonte fisso. HbA1c fuori target esiste a 3 e 5 anni. 3 e 5 anni usano la coorte 2019, 10 anni la globale.")
pref = o2.radio("Modello", ["automatico", "nucleo", "lab"], horizontal=True, help="Nucleo: pochi ingressi. Lab: aggiunge esami (eGFR, pressione, colesterolo). Automatico: il più ricco tra quelli compilati.")

# ---- 2. ingressi ----
ob, fac = [], []
for e in scelti:
    o, f = motore.ingressi_richiesti(doc, e["chiave"], anni, pref)
    ob += [x for x in o if x not in ob]
    fac += [x for x in f if x not in fac]
fac = [x for x in fac if x not in ob]
valori = {}

st.subheader("2. Dati del paziente")
if not scelti:
    st.info("Scegli almeno un esito.")


def _campo(n, facoltativo):
    r = doc["ingressi"][n]
    etichetta = f"{r['etichetta']} ({r['unita']})" + (" · facoltativo" if facoltativo else "")
    if n == "sesso_M":
        s = st.selectbox("Sesso", ["", "Maschio", "Femmina"], key=n)
        valori[n] = None if s == "" else (1.0 if s == "Maschio" else 0.0)
    else:
        valori[n] = st.number_input(etichetta, value=None, step=1.0, key=n, help=f"Intervallo abituale: {r['p1']:.4g}-{r['p99']:.4g}")


diretti = [n for n in ob if n not in motore.DERIVATI]
facolt = [n for n in fac if n not in motore.DERIVATI]
g = st.columns(2)
for i, n in enumerate(diretti):
    with g[i % 2]:
        _campo(n, False)
if facolt:
    with st.expander("Esami facoltativi (aggiungono il modello lab)"):
        for n in facolt:
            _campo(n, True)

if motore.DERIVATI & set(ob + fac):
    st.subheader("3. Terapia antidiabetica alla visita indice")
    st.caption("Il punteggio P e il numero di principi attivi si calcolano da qui: scegli ogni principio attivo e, dove richiesto, la dose giornaliera totale (mg/settimana per semaglutide sottocute, dulaglutide, tirzepatide). Le combinazioni precostituite vanno scomposte nei singoli principi attivi.")
    elenco = potenze.principi_attivi()
    scelti_pa = st.multiselect("Principi attivi", list(elenco), format_func=lambda k: elenco[k]["etichetta"])
    scelte = {}
    for pa in scelti_pa:
        u = elenco[pa]["unita"]
        if u:
            scelte[pa] = st.number_input(f"{elenco[pa]['etichetta']}: dose ({u})", value=None, min_value=0.0, key="dose_" + pa)
        else:
            st.write(f"{elenco[pa]['etichetta']}: potenza fissa, nessuna dose richiesta.")
            scelte[pa] = None
    P, npa, mancanti = potenze.terapia(scelte)
    valori["P"], valori["n_principi_attivi"] = P, (npa if npa > 0 else None)
    if not scelti_pa:
        st.info("Scegli almeno un principio attivo.")
    elif mancanti:
        st.info("Inserisci la dose di: " + ", ".join(elenco[x]["etichetta"] for x in mancanti) + ".")
    else:
        st.write(f"Punteggio P: **{P}** · principi attivi: **{npa}**")

# ---- conferme di popolazione ----
conferme = {}
pop = [(e, motore.POPOLAZIONI[e["chiave"]]) for e in scelti if e["chiave"] in motore.POPOLAZIONI]
if pop:
    st.subheader("Conferme di popolazione")
    for testo in dict.fromkeys(t for _, t in pop):
        conferme[testo] = st.checkbox("Confermo: " + testo, key="pop_" + testo)

# ---- 3. stato degli esiti ----
nome_var = {k: v["etichetta"] for k, v in doc["ingressi"].items()}
risultati = []
for e in scelti:
    ok_pop = conferme.get(motore.POPOLAZIONI.get(e["chiave"]), True) if e["chiave"] in motore.POPOLAZIONI else True
    r = motore.calcola(doc, e["chiave"], anni, valori, pref, ok_pop)
    r["info"] = e
    risultati.append(r)

st.subheader("Stato degli esiti")
for r in risultati:
    e = r["info"]
    if r["stato"] == "ok":
        st.markdown(f"- {e['etichetta']}: pronto, modello {r['modello']['modello']}")
    elif r["stato"] == "mancano":
        st.markdown(f"- {e['etichetta']}: mancano " + ", ".join(nome_var.get(x, x) for x in r["mancanti"]))
    elif r["stato"] == "popolazione":
        st.markdown(f"- {e['etichetta']}: serve la conferma di popolazione")
    else:
        st.markdown(f"- {e['etichetta']}: non disponibile a {anni} anni")

# ---- risultati ----
if st.button("Calcola gli esiti selezionati", type="primary"):
    st.session_state["calcolati"] = [
        {"chiave": r["esito"], "breve": r["info"]["breve"], "etichetta": r["info"]["etichetta"], "stato": r["stato"], "anni": r["anni"],
         "rischio": r["rischio"], "modello": r["modello"], "avvisi": r["avvisi"], "debole": r["info"]["debole"],
         "esplorativo": r["info"]["esplorativo"], "requisiti": r["info"]["requisiti"]} for r in risultati]
calc = st.session_state.get("calcolati")
if calc:
    pronti = [r for r in calc if r["stato"] == "ok"]
    st.subheader("Risultati")
    if len(pronti) >= 3:
        scala = st.radio("Scala del radar", [100, 50], horizontal=True, format_func=lambda s: f"0-{s}%")
        nomi = [f"{r['breve']} {100 * r['rischio']:.0f}%" for r in pronti]
        val = [min(100 * r["rischio"], scala) for r in pronti]
        fig = go.Figure(go.Scatterpolar(r=val + val[:1], theta=nomi + nomi[:1], fill="toself", mode="lines+markers", line=dict(color="#2a78d6", width=2)))
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, scala], ticksuffix="%")), showlegend=False, margin=dict(l=60, r=60, t=20, b=20), height=380)
        st.plotly_chart(fig, width="stretch")
    elif pronti:
        st.info("Il radar richiede almeno 3 esiti calcolati: sotto trovi i valori.")
    righe = []
    for r in calc:
        if r["stato"] == "ok":
            m = r["modello"]
            righe.append({"Esito": r["etichetta"], "Anni": r["anni"], "Rischio": f"{100 * r['rischio']:.1f}%", "Modello": m["modello"],
                          "Coorte": m["coorte"], "AUC": f"{m['auc_fuori_campione']:.2f}", "N": m["n"], "Eventi": m["eventi"], "O/E": f"{m['o_su_e_fuori_campione']:.2f}"})
        else:
            righe.append({"Esito": r["etichetta"], "Anni": r["anni"], "Rischio": "non calcolato", "Modello": None, "Coorte": None, "AUC": None, "N": None, "Eventi": None, "O/E": None})
    st.dataframe(righe, hide_index=True, width="stretch")
    for r in pronti:
        if r["debole"]:
            st.warning(f"{r['etichetta']}: discriminazione bassa (AUC 0,56-0,66), usare con cautela.")
        if r["esplorativo"]:
            st.info(f"{r['etichetta']}: esito esplorativo.")
        if r["requisiti"]:
            st.info(f"{r['etichetta']}: {r['requisiti']}")
        for a in r["avvisi"]:
            st.warning(f"{r['etichetta']}: {a}")
    st.caption("Le probabilità sono stime di ricerca dalla coorte di Rimini, non validate esternamente. Le popolazioni dei modelli sono descritte nel protocollo.")
