"""Gibt den Stand für das Dashboard als JSON aus.
Aufruf: ariadne uebersicht
Nur lesend."""
import json

from kern.uebersicht import uebersicht

if __name__ == "__main__":
    print(json.dumps(uebersicht(), ensure_ascii=False))
