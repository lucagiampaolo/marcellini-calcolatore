# Calcolatore di rischio Marcellini Index (sola ricerca)

App Streamlit che stima la probabilità di esiti in pazienti con diabete tipo 2, con modelli sviluppati sul registro diabetologico di Rimini.
Non è un dispositivo medico, non sostituisce il giudizio clinico, non è validata esternamente.

## Contenuto
- `app.py`: interfaccia multi-esito: checklist degli esiti, orizzonte, modello nucleo/lab/automatico, ingressi richiesti dai soli esiti scelti, terapia con dose (P e numero di principi attivi calcolati dall'app), radar e tabella dei risultati.
- `complicanze.py`, `complicanze.json`: inserimento guidato di TOD e DCSI. Si scelgono per distretto le complicanze documentate all'indice; TOD_ER_max = massimo dei punti TOD, DCSI = somma dei massimi per dominio, ASCVD pregressa dalla classificazione. Tabelle da `Marcellini_Index_Allegati_v2.xlsx` (nessun dato di pazienti, 137 voci con effetto).
- `potenze.py`, `potenze.json`: potenza dei principi attivi per dose (copia di `mi/potenze.yaml`, versione 2026-10-31).
- `motore.py`: calcolo dal file dei modelli.
- `calcolatore_modelli.json`: solo coefficienti, medie, rischio cumulativo di base, intervalli 1-99 percentile e prestazioni aggregate. Nessun dato per paziente.
- `tests/`: test del motore, delle potenze e dell'app (esito multiplo con radar).

## Uso
`pip install -r requirements.txt` poi `streamlit run app.py`. Test: `python -m pytest tests -q`.

## Note
- P non si inserisce a mano: si scelgono i principi attivi e la dose giornaliera (mg/settimana per semaglutide sottocute, dulaglutide, tirzepatide). Senza dose P non è calcolato.
- Il radar richiede almeno 3 esiti calcolati; HbA1c fuori target esiste a 3 e 5 anni, il tempo in target ha orizzonte fisso.
- Coorte 2019 per 3 e 5 anni, globale per 10 anni.
- Il tempo in target è valido solo con almeno 3 misure di HbA1c tra i mesi 6 e 36 e una dal mese 36 entro 120 giorni; la versione con tolleranza 365 giorni è esplorativa.
- Tod, composito non fatale e ASCVD hanno discriminazione bassa.
- Con Streamlit i valori inseriti arrivano al server dell'app: non inserire dati identificativi.
- Pubblicazione subordinata al parere del DPO.
