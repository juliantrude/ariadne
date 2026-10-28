"""T7: Wie zuverlässig ist der Prüfer? Läuft über pruefer-validierung/paare.jsonl.

Jede Zeile: {"antwort": "...", "zitate": [{"zitat","datei","seite","absatz"}], "erwartet": "ja"|"nein", "fehlerart": "..."}
Zielwerte (Abschnitt 8.5): mindestens 90 % der Fehler erkannt ("nein" oder "unklar"), höchstens 20 % Fehlalarme.
Aufruf: ariadne validiere_pruefer [--modell claude-haiku-5-5]
Das Ergebnis gehört in die README, damit jeder Nutzer die Fehlerrate seines Prüfers kennt."""
import argparse
import json
from pathlib import Path

from kern.basis import PLUGIN, jetzt
from kern.pruefer import _eingabe, rufe_modell


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--modell", default="claude-haiku-5-5")
    p.add_argument("--datei", default=str(PLUGIN / "pruefer-validierung" / "paare.jsonl"))
    a = p.parse_args()
    paare = [json.loads(z) for z in Path(a.datei).read_text().splitlines() if z.strip()]
    treffer = fehlalarm = fehler_n = ok_n = 0
    zeilen = []
    for i, paar in enumerate(paare, 1):
        urteil = rufe_modell(a.modell, _eingabe(paar["antwort"], paar["zitate"]))["gesamt"]
        if paar["erwartet"] == "nein":
            fehler_n += 1
            treffer += urteil in ("nein", "unklar")
        else:
            ok_n += 1
            fehlalarm += urteil != "ja"
        zeilen.append({"nr": i, "erwartet": paar["erwartet"], "urteil": urteil, "fehlerart": paar.get("fehlerart")})
        print(f"{i:3d} erwartet {paar['erwartet']:4} urteil {urteil:6} {paar.get('fehlerart', '')}")
    erkannt = treffer / fehler_n if fehler_n else float("nan")
    alarme = fehlalarm / ok_n if ok_n else float("nan")
    print(f"\nModell {a.modell}: {fehler_n} Fehlerpaare, erkannt {erkannt:.0%} (Ziel ≥ 90 %); "
          f"{ok_n} korrekte Paare, Fehlalarme {alarme:.0%} (Ziel ≤ 20 %)")
    ziel = PLUGIN / "pruefer-validierung" / f"ergebnis-{jetzt():%Y-%m-%d}-{a.modell}.json"
    ziel.write_text(json.dumps({"modell": a.modell, "erkannt": erkannt, "fehlalarme": alarme, "paare": zeilen}, indent=1))


if __name__ == "__main__":
    main()
