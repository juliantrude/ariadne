"""Ebene ② der Quellenprüfung: Stützt das Zitat die Aussage? Gibt es unmarkierte Fachaussagen?

Probabilistisch. Ein günstiges Modell (Haiku) in frischem Kontext, Eskalation bei "unklar".
Ungültiges JSON und Zeitüberschreitung gelten als "unklar", nie als "ja".
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from kern.basis import konfig
from kern.quellen import hat_belege


def _cfg() -> dict:
    return {"modell": "claude-haiku-5-5", "eskalation": "claude-sonnet-5-5", "timeout_s": 90,
            "min_zeichen": 400, **konfig().get("pruefer", {})}


def enthaelt_fachaussagen(antwort: str) -> bool:
    """Grobe Vorauswahl, damit nicht jede Rückfrage ein Prüfmodell kostet."""
    if hat_belege(antwort):
        return True
    return len(antwort) >= _cfg()["min_zeichen"]


def _eingabe(antwort: str, zitate: list[dict]) -> str:
    teile = [(Path(__file__).resolve().parents[1] / "pruefer_prompt.md").read_text(), "\n## Antwort des Tutors\n", antwort,
             "\n## Zitierte Stellen mit Absatz\n"]
    for z in zitate:
        teile.append(f'- {z["datei"]} S. {z["seite"]}: "{z["zitat"]}"\n  Absatz: {z["absatz"]}\n')
    if not zitate:
        teile.append("(keine)\n")
    return "".join(teile)


def _json_aus(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return d if d.get("gesamt") in ("ja", "nein", "unklar") else None


def rufe_modell(modell: str, eingabe: str) -> dict:
    """Ein Claude-Code-Aufruf im Druckmodus. Läuft in einem leeren Ordner ohne Projekt- und
    Nutzereinstellungen, damit weder CLAUDE.md noch Hooks den Prüfer beeinflussen."""
    with tempfile.TemporaryDirectory(prefix="ariadne-pruefer-") as leer:
        try:
            r = subprocess.run(
                ["claude", "-p", "--model", modell, "--output-format", "json", "--tools", "",
                 "--no-session-persistence", "--setting-sources", "project"],
                input=eingabe, capture_output=True, text=True, cwd=leer, timeout=_cfg()["timeout_s"],
                env={**os.environ, "ARIADNE_PRUEFER": "1"},
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {"gesamt": "unklar", "fehler": type(e).__name__}
    try:
        ergebnis = json.loads(r.stdout).get("result", "")
    except json.JSONDecodeError:
        ergebnis = r.stdout
    return _json_aus(ergebnis) or {"gesamt": "unklar", "fehler": "kein gültiges JSON", "roh": ergebnis[:500]}


def pruefe(antwort: str, zitate: list[dict], rufe=rufe_modell) -> dict:
    cfg = _cfg()
    eingabe = _eingabe(antwort, zitate)
    urteil = rufe(cfg["modell"], eingabe)
    urteil["modell"] = cfg["modell"]
    if urteil["gesamt"] == "unklar":
        urteil = rufe(cfg["eskalation"], eingabe)
        urteil["modell"] = cfg["eskalation"]
    return urteil


def befunde(urteil: dict) -> list[str]:
    return [f'{a.get("stuetzt")}: "{a.get("text", "")[:80]}" – {a.get("grund", "")}'
            for a in urteil.get("aussagen", []) if a.get("stuetzt") in ("nein", "fehlt")]
