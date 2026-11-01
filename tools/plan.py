"""Kapitel, Lehrplan, Meilensteine, Fortschritt. Einziger Schreibweg nach learner/kapitel/.

  ariadne plan neu os "Betriebssysteme" --konzepte os. --ziel klausur --datum 2027-02-15 --stichwort Betriebssysteme
  ariadne plan vorwissen-fertig os --zusammenfassung "..." --gedaechtnis "Documents/uni/user-studienplanung"
  ariadne plan vorschlag os --stunden 5 --sitzungen 3 --energie mittel [--gliederung gliederung.json] [--notiz "..."]
  ariadne plan vereinbaren os --zustimmung "<wörtlicher Satz des Lernenden>"
  ariadne plan zuruecknehmen os       (fälschlich vereinbart -> wieder Entwurf)
  ariadne plan schaerfen os M2 --pruefung '{"art": "challenge", "beschreibung": "...", "kriterien": ["..."]}'
  ariadne plan pruefung-start os M1
  ariadne plan item os M1 --konzept os.vm.tlb --ergebnis richtig --sicherheit 4
  ariadne plan item os M2 --kriterium "Messung erklärt" --ergebnis teilweise --sicherheit 3
  ariadne plan auswerten os M1
  ariadne plan status [os]            (ohne Kapitel: alle)
  ariadne plan zeige os               (Plan als JSON)
"""
import argparse
import json
import sys
from pathlib import Path

from kern import lernermodell as lm
from kern import planung as pl

ZUSTAND = {"bestanden": "✓", "offen": "·", "faellig": "!", "verpasst": "✗"}


def balken(anteil: float, breite: int = 24) -> str:
    voll = round(max(0.0, min(anteil, 1.0)) * breite)
    return "█" * voll + "░" * (breite - voll)


def zeige_status(s: dict) -> str:
    z = [f"{s['titel']} ({s['kapitel']})"]
    if s["ziel"]["datum"]:
        z.append(f"  Ziel: {s['ziel']['art']} am {s['ziel']['datum']}")
    k = s["konzepte"]
    z.append(f"  Konzepte: {k['gesamt']} · sitzen {k['sitzen']} · im Aufbau {k['im_aufbau']} · neu {k['neu']}")
    z.append(f"  Vorwissensanalyse: {s['vorwissen']}")
    p = s["plan"]
    if p:
        b = p["budget"]
        z.append(f"  Plan v{p['version']} ({p['status']}): {p['start']} bis {p['ende']} · "
                 f"{b['stunden_pro_woche']} h/Woche in {b['sitzungen_pro_woche']} Sitzungen à {b['sitzung_min']} min · "
                 f"Energie {b['energie']}")
        if not p["machbarkeit"]["machbar"]:
            m = p["machbarkeit"]
            z.append(f"  ACHTUNG nicht machbar bis Ziel: {m['fehlende_tage']} Tage zu spät, "
                     f"nötig wären {m['noetige_stunden_pro_woche']} h/Woche")
        z.append(f"  Ist  {balken(p['ist_anteil'])} {p['ist_anteil']:.0%}")
        z.append(f"  Soll {balken(p['soll_anteil'])} {p['soll_anteil']:.0%}")
        r = p["rueckstand_tage"]
        lage = "im Plan" if r == 0 else f"{r} Tage hinter dem Plan" if r > 0 else f"{-r} Tage voraus"
        z.append(f"  Zeitplan: {lage}")
        z.append(f"  Lernzeit diese Woche: {p['lernzeit_woche_min']} von {p['vereinbart_woche_min']} min (gemessen)")
        z.append("  Meilensteine:")
        for m in p["meilensteine"]:
            versuch = f" · letzter Versuch {m['letzter_versuch']:.0%}" if m["letzter_versuch"] is not None else ""
            z.append(f"    {ZUSTAND[m['zustand']]} {m['id']} {m['zieldatum']}  {m['titel'][:40]:40}  "
                     f"Konzepte {m['konzepte_sitzen']} · {m['pruefung'] if m['scharf'] else 'Nebel'}{versuch}")
        if p["neuverhandeln"]:
            z.append(f"  NEUVERHANDLUNG EMPFOHLEN: {'; '.join(p['neuverhandeln'])}")
    z.append(f"  Nächster Schritt: {s['naechster_schritt']}")
    return "\n".join(z)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="plan.py")
    sub = p.add_subparsers(dest="befehl", required=True)

    n = sub.add_parser("neu")
    n.add_argument("id"); n.add_argument("titel")
    n.add_argument("--konzepte", required=True, help="kommagetrennt; 'os.vm.' = alle mit diesem Präfix")
    n.add_argument("--ziel", default="verstaendnis", help="klausur | projekt | verstaendnis | ...")
    n.add_argument("--datum"); n.add_argument("--beschreibung", default="")
    n.add_argument("--stichwort", action="append", default=[])

    v = sub.add_parser("vorwissen-fertig")
    v.add_argument("id"); v.add_argument("--zusammenfassung", required=True)
    v.add_argument("--gedaechtnis", action="append", default=[], help="Ref der genutzten Gedächtniseinträge")

    o = sub.add_parser("vorschlag")
    o.add_argument("id"); o.add_argument("--stunden", type=float, required=True)
    o.add_argument("--sitzungen", type=int, required=True)
    o.add_argument("--energie", choices=pl.ENERGIE, required=True)
    o.add_argument("--gliederung", help="JSON-Datei: [{titel, konzepte, pruefung:{art, beschreibung, kriterien}}]")
    o.add_argument("--start"); o.add_argument("--notiz", default="")

    e = sub.add_parser("vereinbaren")
    e.add_argument("id"); e.add_argument("--zustimmung", required=True)

    zr = sub.add_parser("zuruecknehmen")
    zr.add_argument("id")

    sc = sub.add_parser("schaerfen")
    sc.add_argument("id"); sc.add_argument("meilenstein")
    sc.add_argument("--pruefung", required=True, help="JSON oder Pfad zu einer JSON-Datei")
    sc.add_argument("--titel")

    ps = sub.add_parser("pruefung-start")
    ps.add_argument("id"); ps.add_argument("meilenstein")

    i = sub.add_parser("item")
    i.add_argument("id"); i.add_argument("meilenstein")
    i.add_argument("--konzept", default=""); i.add_argument("--kriterium", default="")
    i.add_argument("--ergebnis", choices=sorted(pl.ERGEBNIS_PUNKTE), required=True)
    i.add_argument("--sicherheit", type=int, required=True)

    a = sub.add_parser("auswerten")
    a.add_argument("id"); a.add_argument("meilenstein")

    s = sub.add_parser("status")
    s.add_argument("id", nargs="?")
    s.add_argument("--json", action="store_true")

    z = sub.add_parser("zeige")
    z.add_argument("id")

    x = p.parse_args(argv)
    try:
        if x.befehl == "neu":
            kap = pl.neu(x.id, x.titel, [k.strip() for k in x.konzepte.split(",") if k.strip()],
                         x.ziel, x.datum, x.beschreibung, x.stichwort)
            print(f"Kapitel {kap['id']} mit {len(kap['konzepte'])} Konzepten angelegt. Nächster Schritt: /ariadne:vorwissen {kap['id']}")
        elif x.befehl == "vorwissen-fertig":
            kap = pl.vorwissen_abschliessen(x.id, x.zusammenfassung, x.gedaechtnis)
            start = kap["vorwissen"]["start_beherrschung"]
            print(f"Vorwissen erfasst. Startbeherrschung: {json.dumps(start, ensure_ascii=False)}")
            if kap["vorwissen"]["ohne_diagnose"]:
                print(f"Ohne Diagnose (zählen als 0): {', '.join(kap['vorwissen']['ohne_diagnose'])}")
        elif x.befehl == "vorschlag":
            gl = json.loads(Path(x.gliederung).read_text()) if x.gliederung else None
            kap = pl.vorschlag(x.id, x.stunden, x.sitzungen, x.energie, gl, x.start, x.notiz)
            print(zeige_status(pl.status(x.id)))
            print(json.dumps({"machbarkeit": kap["plan"]["machbarkeit"],
                              "minuten_gesamt": kap["plan"]["minuten_gesamt"]}, ensure_ascii=False))
        elif x.befehl == "vereinbaren":
            pl.vereinbaren(x.id, x.zustimmung)
            print(zeige_status(pl.status(x.id)))
        elif x.befehl == "zuruecknehmen":
            pl.zuruecknehmen(x.id)
            print(f"Plan {x.id} ist wieder ein Entwurf.")
        elif x.befehl == "schaerfen":
            quelle = Path(x.pruefung)
            pruefung = json.loads(quelle.read_text() if quelle.is_file() else x.pruefung)
            m = pl.schaerfen(x.id, x.meilenstein, pruefung, x.titel)
            print(f"{m['id']} ist jetzt scharf: {m['pruefung']['art']} – {m['pruefung'].get('beschreibung', '')}")
        elif x.befehl == "pruefung-start":
            m = pl.pruefung_start(x.id, x.meilenstein)
            ziel = m["pruefung"].get("kriterien") or m["konzepte"]
            print(f"{m['id']} ({m['pruefung']['art']}) gestartet. Zu prüfen, gemischt: {', '.join(ziel)}")
        elif x.befehl == "item":
            laufend = pl.pruefung_item(x.id, x.meilenstein, x.ergebnis, x.sicherheit, x.konzept, x.kriterium)
            print(f"{len(laufend['items'])} Items erfasst.")
        elif x.befehl == "auswerten":
            v = pl.pruefung_auswerten(x.id, x.meilenstein)
            print(f"{x.meilenstein}: {'BESTANDEN' if v['bestanden'] else 'nicht bestanden'} mit {v['quote']:.0%}"
                  + (f" · zu wiederholen: {', '.join(v['schwache'])}" if v["schwache"] else ""))
        elif x.befehl == "status":
            ids = [x.id] if x.id else [k["id"] for k in pl.alle()]
            if not ids:
                print("Noch kein Kapitel. Starte mit /ariadne:kapitel.")
            stati = [pl.status(i) for i in ids]
            print(json.dumps(stati, ensure_ascii=False, indent=1) if x.json else "\n\n".join(map(zeige_status, stati)))
        elif x.befehl == "zeige":
            print(json.dumps(pl.lade(x.id)["plan"], ensure_ascii=False, indent=1))
        return 0
    except (pl.Fehler, lm.Fehler) as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
