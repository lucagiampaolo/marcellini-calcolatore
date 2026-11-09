# Calcolatore di rischio Marcellini Index (sola ricerca)

App Streamlit che stima la probabilità di esiti in pazienti con diabete tipo 2, con modelli sviluppati sul registro diabetologico di Rimini.
Non è un dispositivo medico, non sostituisce il giudizio clinico, non è validata esternamente.

## Contenuto
- `app.py`: interfaccia (scelta di esito, orizzonte, modello nucleo/lab/automatico).
- `motore.py`: calcolo dal file dei modelli.
- `calcolatore_modelli.json`: solo coefficienti, medie, rischio cumulativo di base, intervalli 1-99 percentile e prestazioni aggregate. Nessun dato per paziente.
- `tests/`: test del motore e dell'app.

## Uso
`pip install -r requirements.txt` poi `streamlit run app.py`. Test: `python -m pytest tests -q`.

## Note
- Coorte 2019 per 3 e 5 anni, globale per 10 anni.
- Il tempo in target è valido solo con almeno 3 misure di HbA1c tra i mesi 6 e 36 e una dal mese 36 entro 120 giorni; la versione con tolleranza 365 giorni è esplorativa.
- Tod, composito non fatale e ASCVD hanno discriminazione bassa.
- Con Streamlit i valori inseriti arrivano al server dell'app: non inserire dati identificativi.
- Pubblicazione subordinata al parere del DPO.
