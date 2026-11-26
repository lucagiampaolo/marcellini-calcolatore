"""Rende importabile il pacchetto `mi` (cartella superiore) quando disponibile, cosi' il test di coerenza con mi.drugs non viene saltato. L'app resta indipendente da `mi`."""
import sys
from pathlib import Path

radice = Path(__file__).resolve().parents[2]
if (radice / "mi").is_dir() and str(radice) not in sys.path:
    sys.path.insert(0, str(radice))
