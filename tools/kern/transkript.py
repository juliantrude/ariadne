"""Liest das Sitzungsprotokoll von Claude Code (transcript_path, JSONL).

Das Format ist intern und kann sich zwischen Versionen ändern. Deshalb ist alles,
was davon abhängt, hier gekapselt und mit gespeicherten Beispielen getestet (T10).
"""
from __future__ import annotations

import json
from pathlib import Path


def _zeilen(pfad: str | Path) -> list[dict]:
    raus = []
    p = Path(pfad) if pfad else None
    if p is None or not p.is_file():
        return raus
    for zeile in p.read_text(errors="replace").splitlines():
        try:
            raus.append(json.loads(zeile))
        except json.JSONDecodeError:
            continue
    return raus


def _texte(inhalt) -> list[str]:
    if isinstance(inhalt, str):
        return [inhalt]
    return [b.get("text", "") for b in inhalt or [] if isinstance(b, dict) and b.get("type") == "text"]


def _ist_echte_eingabe(e: dict) -> bool:
    """Eine Nutzereingabe, kein Tool-Ergebnis und keine Meta-Nachricht."""
    if e.get("type") != "user" or e.get("isMeta") or e.get("isSidechain"):
        return False
    inhalt = e.get("message", {}).get("content")
    if isinstance(inhalt, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in inhalt):
        return False
    return True


def letzte_antwort(pfad: str | Path) -> str:
    """Alle Texte des Assistenten seit der letzten echten Nutzereingabe."""
    texte: list[str] = []
    for e in _zeilen(pfad):
        if e.get("isSidechain"):
            continue
        if _ist_echte_eingabe(e):
            texte = []
        elif e.get("type") == "assistant":
            texte += _texte(e.get("message", {}).get("content"))
    return "\n".join(t for t in texte if t.strip())


def nutzer_eingaben(pfad: str | Path) -> list[str]:
    return ["\n".join(_texte(e.get("message", {}).get("content")))
            for e in _zeilen(pfad) if _ist_echte_eingabe(e)]
