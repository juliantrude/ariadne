"""SessionStart: Sitzung registrieren, Tutor-Regeln einspielen, fällige Wiederholungen und Stand der Kapitel einblenden.

Die Regeln (regeln.md) liegen im Plugin, nicht im Lern-Repo: Der Tutor liest sie, kann sie aber nicht
nebenbei im Arbeitsverzeichnis ändern. SessionStart läuft auch nach /clear und nach dem Verdichten erneut."""
import json
import os
import sys

from _pfad import DATEN, PLUGIN, aus, ereignis

if aus():
    sys.exit(0)

from kern import lernermodell as lm  # noqa: E402
from kern import planung as pl  # noqa: E402
from kern.basis import sitzungs_ordner  # noqa: E402

ev = ereignis()
sid = ev.get("session_id", "ohne-sitzung")
(DATEN / "sitzungen").mkdir(exist_ok=True)
(DATEN / "sitzungen" / ".aktuell").write_text(sid)
if env_datei := os.environ.get("CLAUDE_ENV_FILE"):
    with open(env_datei, "a") as f:
        f.write(f"export ARIADNE_SESSION={sid}\nexport ARIADNE_ROOT={DATEN}\n")
        if ev.get("transcript_path"):
            f.write(f"export ARIADNE_TRANSCRIPT={ev['transcript_path']}\n")
os.environ["ARIADNE_SESSION"] = sid
sitzungs_ordner()

regeln = (PLUGIN / "regeln.md").read_text().replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN))
zeilen = [regeln, "", f"[Ariadne] Sitzungsstart im Lern-Repo {DATEN}."]
faellig = lm.lade() and lm.faellig()
if faellig:
    ids = ", ".join(k["id"] for k in faellig[:12])
    zeilen.append(f"Fällige Wiederholungen ({len(faellig)}): {ids}. Zuerst /ariadne:wiederholen anbieten.")
else:
    zeilen.append("Keine fälligen Wiederholungen.")

for kap in pl.alle():
    try:
        s = pl.status(kap["id"])
    except Exception as e:  # ein kaputtes Kapitel darf den Start nicht verhindern
        zeilen.append(f"Kapitel {kap.get('id')}: Status nicht lesbar ({e}).")
        continue
    p = s["plan"]
    teil = f"Kapitel {s['kapitel']} ({s['titel']}): "
    if not p:
        teil += f"noch kein Plan, Vorwissen {s['vorwissen']}."
    else:
        r = p["rueckstand_tage"]
        lage = "im Plan" if r == 0 else f"{r} Tage hinterher" if r > 0 else f"{-r} Tage voraus"
        teil += (f"Plan v{p['version']} {p['status']}, Ist {p['ist_anteil']:.0%} / Soll {p['soll_anteil']:.0%}, {lage}, "
                 f"Lernzeit Woche {p['lernzeit_woche_min']}/{p['vereinbart_woche_min']} min.")
        faellige_ms = [m["id"] for m in p["meilensteine"] if m["zustand"] in ("faellig", "verpasst")]
        if faellige_ms:
            teil += f" Meilenstein fällig: {', '.join(faellige_ms)}."
        if p["neuverhandeln"]:
            teil += f" Neuverhandlung ansprechen: {'; '.join(p['neuverhandeln'])}."
    teil += f" Nächster Schritt: {s['naechster_schritt']}."
    zeilen.append(teil)
if not pl.alle():
    zeilen.append("Noch kein Kapitel. Für ein neues Thema: /ariadne:kapitel.")

print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n".join(zeilen)}},
                 ensure_ascii=False))
