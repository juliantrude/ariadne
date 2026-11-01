"""Hält Antworten zurück, bis der Stop-Hook entschieden hat. So sieht der Lernende nur die letzte Fassung.

Claude Code startet MessageDisplay (je Stapel fertiger Zeilen) und Stop gleichzeitig, und nur MessageDisplay
bestimmt, was auf dem Schirm landet. Alles bis auf den letzten Stapel wird deshalb gesammelt und durch nichts
ersetzt. Im letzten Stapel wartet die Anzeige auf das Urteil von Stop. Geprüft wird nur dort.

Zwischentext vor einem Werkzeugaufruf bekommt kein Stop. Meldet sich Stop nicht binnen FENSTER_S, gilt die
Nachricht als Zwischentext und wird gezeigt. Im Zweifel erscheint Text, statt zu verschwinden.
"""
from __future__ import annotations

import hashlib
import shutil
import time
from pathlib import Path

FENSTER_S = 2.0
FRIST_S = 245.0  # etwas über dem timeout des Stop-Hooks, deutlich unter dem von MessageDisplay
TAKT_S = 0.05
ALT_S = 3600


def _ordner(wurzel: Path, sid: str) -> Path:
    basis = wurzel / "sitzungen" / ".anzeige"
    ordner = basis / sid
    ordner.mkdir(parents=True, exist_ok=True)
    (basis / ".gitignore").write_text("*\n")
    return ordner


def _schluessel(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:16]


def stop_beginnt(wurzel: Path, sid: str, antwort: str) -> None:
    o, k = _ordner(wurzel, sid), _schluessel(antwort)
    (o / f"{k}.urteil").unlink(missing_ok=True)
    (o / f"{k}.laeuft").touch()


def stop_entscheidet(wurzel: Path, sid: str, antwort: str, zeigen: bool) -> None:
    o, k = _ordner(wurzel, sid), _schluessel(antwort)
    tmp = o / f"{k}.tmp"
    tmp.write_text("zeigen" if zeigen else "verbergen")
    tmp.rename(o / f"{k}.urteil")


def _warte_auf_urteil(ordner: Path, k: str, fenster_s: float, frist_s: float) -> bool:
    laeuft, urteil = ordner / f"{k}.laeuft", ordner / f"{k}.urteil"
    beginn = time.monotonic()
    while True:
        vergangen = time.monotonic() - beginn
        if urteil.exists():
            return urteil.read_text() != "verbergen"
        if vergangen >= (frist_s if laeuft.exists() else fenster_s):
            return True
        time.sleep(TAKT_S)


def _aufraeumen(ordner: Path, k: str) -> None:
    (ordner / f"{k}.laeuft").unlink(missing_ok=True)
    (ordner / f"{k}.urteil").unlink(missing_ok=True)
    grenze = time.time() - ALT_S
    for p in ordner.iterdir():
        if p.stat().st_mtime < grenze:
            shutil.rmtree(p) if p.is_dir() else p.unlink()


def halte(ev: dict, wurzel: Path, fenster_s: float = FENSTER_S, frist_s: float = FRIST_S) -> str:
    """Der Text, den Claude Code für diesen Stapel anzeigen soll."""
    ordner = _ordner(wurzel, ev.get("session_id", "ohne-sitzung"))
    nachricht = ordner / ev["message_id"]
    nachricht.mkdir(exist_ok=True)
    (nachricht / f"{ev['index']:06d}").write_text(ev["delta"])
    if not ev["final"]:
        return ""

    # Stapel laufen parallel, die früheren können noch unterwegs sein.
    beginn = time.monotonic()
    while len(list(nachricht.iterdir())) <= ev["index"] and time.monotonic() - beginn < fenster_s:
        time.sleep(TAKT_S)
    text = "".join(p.read_text() for p in sorted(nachricht.iterdir()))
    shutil.rmtree(nachricht)

    k = _schluessel(text)
    zeigen = _warte_auf_urteil(ordner, k, fenster_s, frist_s)
    _aufraeumen(ordner, k)
    return text if zeigen else ""
