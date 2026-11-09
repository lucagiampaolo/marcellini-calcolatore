"""Calcolatore di rischio Marcellini Index (solo ricerca). Streamlit: streamlit run app.py"""
import streamlit as st

import motore

st.set_page_config(page_title="Marcellini Index - calcolatore di ricerca", layout="centered")
doc = motore.carica()

st.title("Calcolatore di rischio - Marcellini Index")
st.warning(doc["disclaimer"] + " Non inserire dati identificativi.")

DEBOLI = {"tod", "composito_nonfatale", "ascvd"}
POPOLAZIONI = {"dcsi_progressione": "Confermo che il DCSI all'indice è 0", "ascvd": "Confermo che il paziente non ha ASCVD pregressa",
               "composito_nonfatale": "Confermo che il paziente non ha ASCVD pregressa"}

esiti = {}
for m in doc["modelli"]:
    esiti.setdefault(m["esito"], m["etichetta"].split(" a ")[0] if m["esito"] == "hba1c_fuori_target" else m["etichetta"])
esito = st.sidebar.selectbox("Esito", list(esiti), format_func=lambda k: esiti[k])
anni_disp = sorted({m["orizzonte_anni"] for m in doc["modelli"] if m["esito"] == esito})
anni = st.sidebar.selectbox("Orizzonte (anni)", anni_disp) if len(anni_disp) > 1 else anni_disp[0]
if len(anni_disp) == 1:
    st.sidebar.write(f"Orizzonte: {anni} anni" + (" (finestra mesi 6-36)" if esito.startswith("tt_") else ""))
pref = st.sidebar.radio("Modello", ["automatico", "nucleo", "lab"], help="Nucleo: pochi ingressi. Lab: con eGFR o altri esami. Automatico: il più ricco tra quelli compilati.")

cand = motore.candidati(doc, esito, anni)
st.caption(f"Coorte di sviluppo: {cand[0]['coorte']}. Modelli disponibili: " + ", ".join(m["modello"] for m in cand) + ".")
if cand[0].get("stato") == "esplorativo":
    st.info("Esito esplorativo.")
if cand[0].get("requisiti"):
    st.info(cand[0]["requisiti"])
if esito in DEBOLI:
    st.warning("Discriminazione bassa (AUC 0,56-0,66): usare con cautela.")

# ingressi: unione delle variabili dei modelli candidati
nomi = []
for m in cand:
    for v in m["variabili"]:
        if v["nome"] not in nomi:
            nomi.append(v["nome"])
valori = {}
st.subheader("Dati del paziente")
for n in nomi:
    r = doc["ingressi"][n]
    if n == "sesso_M":
        s = st.selectbox("Sesso", ["", "Maschio", "Femmina"], key=n)
        valori[n] = None if s == "" else (1.0 if s == "Maschio" else 0.0)
    else:
        valori[n] = st.number_input(f"{r['etichetta']} ({r['unita']})", value=None, step=1.0, key=n, help=f"Intervallo abituale: {r['p1']:.4g}-{r['p99']:.4g}")
ok_pop = True
if esito in POPOLAZIONI:
    ok_pop = st.checkbox(POPOLAZIONI[esito])

if st.button("Calcola"):
    m = motore.scegli(doc, esito, anni, valori, pref)
    if not ok_pop:
        st.error("Il modello vale solo se la condizione sopra è vera.")
    elif m is None:
        st.error("Compila tutti gli ingressi del modello scelto.")
    else:
        p = motore.rischio(m, valori)
        st.metric(f"Probabilità stimata ({m['etichetta']}, {anni} anni, modello {m['modello']})", f"{100 * p:.1f}%")
        st.write(f"Coorte di sviluppo {m['coorte']}: {m['n']} pazienti, {m['eventi']} eventi. AUC fuori campione {m['auc_fuori_campione']:.2f}; osservati/attesi {m['o_su_e_fuori_campione']:.2f}.")
        if m["popolazione"]:
            st.write("Popolazione: " + m["popolazione"] + ".")
        for a in motore.avvisi(doc, m, valori):
            st.warning(a)
