"""FSRS-Wiederholungsplan. Aufruf: ariadne review [faellig|vorschau TAGE]"""
import sys
from datetime import timedelta

from kern import lernermodell as lm
from kern.basis import jetzt


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv[:1] == ["vorschau"]:
        tage = int(argv[1]) if len(argv) > 1 else 7
        for t in range(tage + 1):
            stichtag = jetzt() + timedelta(days=t)
            n = len(lm.faellig(stichtag))
            print(f"{stichtag.date()}  {n:3d} fällig (kumuliert)")
        return 0
    faellig = lm.faellig()
    if not faellig:
        print("Nichts fällig.")
    for k in faellig:
        grund = "Wiederholungspflicht (Stufe 4)" if k.get("pflicht_termin") else "FSRS"
        print(f"{k['id']:32} B{k['beherrschung']}  {grund:30}  {k['titel']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
