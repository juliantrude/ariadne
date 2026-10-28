"""Stop: prüft jede Antwort, bevor sie als fertig gilt.

① Zitate stehen wörtlich auf der Seite, Läufe existieren (deterministisch)
② Haiku: stützt das Zitat die Aussage, gibt es unmarkierte Fachaussagen (probabilistisch, Eskalation)
③ Wiederholungspflicht nach Stufe 4
④ Ein als vereinbart eingetragener Lehrplan hat eine wörtliche Zustimmung des Lernenden im Gespräch
Höchstens zwei Korrekturrunden, danach sichtbare Warnung statt Endlosschleife (T11).
"""
import json
import os
import sys

from _pfad import DATEN, aus, ereignis

if aus():
    sys.exit(0)

from kern import lernermodell as lm  # noqa: E402
from kern import pruefer  # noqa: E402
from kern.basis import jetzt, lies_json, protokoll, schreib_json, sitzungs_ordner  # noqa: E402
from kern.quellen import norm, pruefe_laeufe, pruefe_zitate  # noqa: E402
from kern.transkript import letzte_antwort, nutzer_eingaben  # noqa: E402

MAX_RUNDEN = 2


def wiederholungspflicht_verletzt(sid: str) -> list[str]:
    konzepte = lm.lade()
    ereignisse = [e for e in protokoll(tage=2) if e["sitzung"] == sid]
    fehler = []
    for i, e in enumerate(ereignisse):
        if e["art"] != "stufe" or e["stufe"] != 4:
            continue
        k = konzepte.get(e["konzept"], {})
        spaeter_bewertet = any(x["art"] == "abruf" and x["konzept"] == e["konzept"] for x in ereignisse[i + 1:])
        if not k.get("pflicht_termin") and not spaeter_bewertet:
            fehler.append(f"Wiederholungspflicht: {e['konzept']} erreichte Stufe 4, aber es gibt keinen Wiederholungstermin. "
                          f"Mit 'ariadne lm stufe {e['konzept']} 4' oder einem Abruf über `ariadne lm abruf` nachholen.")
    return fehler


def zustimmung_fehlt(sid: str, transcript: str) -> list[str]:
    eingaben = [norm(t) for t in nutzer_eingaben(transcript)]
    fehler = []
    ereignisse = protokoll(tage=2)
    for i, e in enumerate(ereignisse):
        if e["sitzung"] != sid or e["art"] != "plan_vereinbart":
            continue
        if any(x["art"] == "plan_zurueckgenommen" and x["kapitel"] == e["kapitel"] and x["version"] == e["version"]
               for x in ereignisse[i + 1:]):
            continue
        if not any(norm(e["zustimmung"]) in t for t in eingaben):
            fehler.append(f"Plan {e['kapitel']} v{e['version']} ist als vereinbart eingetragen, aber die Zustimmung "
                          f"„{e['zustimmung'][:60]}“ steht so nicht in den Eingaben des Lernenden. "
                          f"'ariadne plan zuruecknehmen {e['kapitel']}' ausführen und die Zustimmung wörtlich einholen.")
    return fehler


def main() -> None:
    ev = ereignis()
    sid = ev.get("session_id", "ohne-sitzung")
    os.environ.setdefault("ARIADNE_SESSION", sid)
    antwort = ev.get("last_assistant_message") or letzte_antwort(ev.get("transcript_path", ""))

    fehler, zitate = pruefe_zitate(antwort)
    fehler += pruefe_laeufe(antwort, sid)
    urteil = None
    if not fehler and pruefer.enthaelt_fachaussagen(antwort) and not os.environ.get("ARIADNE_OHNE_PRUEFER"):
        urteil = pruefer.pruefe(antwort, zitate)
        if urteil["gesamt"] == "nein":
            fehler += pruefer.befunde(urteil) or ["Prüfer: mindestens eine Aussage nicht gestützt oder unmarkiert."]
    fehler += wiederholungspflicht_verletzt(sid)
    fehler += zustimmung_fehlt(sid, ev.get("transcript_path", ""))

    runden_pfad = DATEN / "sitzungen" / ".stop_runden.json"
    runden = lies_json(runden_pfad, {})
    runde = runden.get(sid, 0) if ev.get("stop_hook_active") else 0

    with open(sitzungs_ordner() / "pruefungen.jsonl", "a") as f:
        f.write(json.dumps({"zeit": jetzt().isoformat(timespec="seconds"), "sitzung": sid, "runde": runde,
                            "zitate": len(zitate), "fehler": fehler, "urteil": urteil}, ensure_ascii=False) + "\n")

    if fehler and runde < MAX_RUNDEN:
        runden[sid] = runde + 1
        schreib_json(runden_pfad, runden)
        print(json.dumps({"decision": "block",
                          "reason": "Ariadne-Prüfung fehlgeschlagen, bitte korrigieren:\n- " + "\n- ".join(fehler)},
                         ensure_ascii=False))
        return
    runden.pop(sid, None)
    schreib_json(runden_pfad, runden)
    if fehler:
        print(json.dumps({"systemMessage": "⚠ Beleg prüfen: Die Antwort hat die Prüfung auch nach zwei Korrekturen "
                                           "nicht bestanden:\n- " + "\n- ".join(fehler)}, ensure_ascii=False))
    elif urteil and urteil["gesamt"] == "unklar":
        print(json.dumps({"systemMessage": f"⚠ Beleg prüfen: Prüfer ({urteil.get('modell')}) war unsicher."},
                         ensure_ascii=False))


main()
