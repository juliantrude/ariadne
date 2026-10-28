"""Einziger Schreibweg ins Lernermodell (learner/). Aufruf: ariadne lm <befehl> ...

Beispiele:
  ariadne lm anlegen os.vm.tlb "Translation Lookaside Buffer" --quelle material/os/skript.pdf#S112 --vor os.vm.seitentabelle
  ariadne lm stufe os.vm.tlb 2 --stelle S1
  ariadne lm stufe os.vm.tlb 4 --notausgang
  ariadne lm abruf os.vm.tlb --richtig --sicherheit 4 [--stufe 0] [--erklaerung-traegt nein] [--schnell]
  ariadne lm vorwissen os.vm.tlb teilweise --sicherheit 3 --selbst 2 --kapitel os [--fehlvorstellung "..."]
  ariadne lm fehlvorstellung os.vm.tlb "TLB-Miss = Page Fault" [--behoben]
  ariadne lm zeige [konzept-präfix]
"""
import argparse
import json
import sys

from kern import lernermodell as lm


def ja_nein(s: str) -> bool:
    return s.lower() in ("ja", "j", "yes", "y", "1", "true")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="lm.py")
    sub = p.add_subparsers(dest="befehl", required=True)

    a = sub.add_parser("anlegen")
    a.add_argument("id"); a.add_argument("titel")
    a.add_argument("--quelle", default=""); a.add_argument("--vor", action="append", default=[])

    s = sub.add_parser("stufe")
    s.add_argument("id"); s.add_argument("stufe", type=int)
    s.add_argument("--stelle", default=""); s.add_argument("--notausgang", action="store_true")

    r = sub.add_parser("abruf")
    r.add_argument("id")
    g = r.add_mutually_exclusive_group(required=True)
    g.add_argument("--richtig", action="store_true"); g.add_argument("--falsch", action="store_true")
    r.add_argument("--sicherheit", type=int, required=True)
    r.add_argument("--stufe", type=int, default=None)
    r.add_argument("--erklaerung-traegt", default="ja")
    r.add_argument("--schnell", action="store_true")
    r.add_argument("--quelle", default="abruf")

    v = sub.add_parser("vorwissen")
    v.add_argument("id"); v.add_argument("ergebnis", choices=sorted(lm.VORWISSEN_BEHERRSCHUNG))
    v.add_argument("--sicherheit", type=int); v.add_argument("--selbst", type=int)
    v.add_argument("--kapitel", default=""); v.add_argument("--fehlvorstellung", default="")

    f = sub.add_parser("fehlvorstellung")
    f.add_argument("id"); f.add_argument("text"); f.add_argument("--behoben", action="store_true")

    z = sub.add_parser("zeige")
    z.add_argument("praefix", nargs="?", default="")

    x = p.parse_args(argv)
    try:
        if x.befehl == "anlegen":
            k = lm.anlegen(x.id, x.titel, x.quelle, x.vor)
        elif x.befehl == "stufe":
            k = lm.stufe(x.id, x.stufe, x.stelle, x.notausgang)
        elif x.befehl == "abruf":
            k = lm.abruf(x.id, richtig=x.richtig, sicherheit=x.sicherheit, stufe=x.stufe,
                         erklaerung_traegt=ja_nein(x.erklaerung_traegt), schnell=x.schnell, quelle=x.quelle)
            h = k["historie"][-1]
            print(f"{x.id}: {h['bewertung']} · Beherrschung {h['beherrschung']} · nächster Termin {k['fsrs']['due'][:10]}")
            return 0
        elif x.befehl == "vorwissen":
            k = lm.vorwissen(x.id, x.ergebnis, x.sicherheit, x.selbst, x.fehlvorstellung, x.kapitel)
        elif x.befehl == "fehlvorstellung":
            k = lm.fehlvorstellung(x.id, x.text, x.behoben)
        else:
            ks = {i: k for i, k in lm.lade().items() if i.startswith(x.praefix)}
            for i, k in ks.items():
                due = (k.get("fsrs") or {}).get("due", "")[:10] or k.get("pflicht_termin", "–")
                offen = sum(not f["behoben"] for f in k["fehlvorstellungen"])
                print(f"{i:32} B{k['beherrschung']}  fällig {due:10}  Fehlvorst. offen {offen}  {k['titel']}")
            return 0
        print(json.dumps({key: k[key] for key in ("id", "beherrschung", "letzte_stufe") if key in k}
                         | {"pflicht_termin": k.get("pflicht_termin"), "faellig": (k.get("fsrs") or {}).get("due")},
                         ensure_ascii=False))
        return 0
    except lm.Fehler as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
