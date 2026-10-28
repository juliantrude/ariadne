"""Gemeinsame Grundlagen: Pfade, Konfiguration, Sitzung, Protokoll, Git."""
from __future__ import annotations

import json
import os
import subprocess
import tomllib
from datetime import date, datetime, timezone
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[2]
MARKER = "ariadne.toml"


def finde_lernrepo(start: Path) -> Path | None:
    """Das Lern-Repo ist das nächste Verzeichnis aufwärts mit einer ariadne.toml."""
    for d in (start, *start.parents):
        if (d / MARKER).is_file():
            return d
    return None


def wurzel() -> Path:
    """Wurzel des Lern-Repos (Daten), nicht des Plugins (Code).
    Reihenfolge: ARIADNE_ROOT (Tests), aufwärts ab dem Arbeitsverzeichnis, CLAUDE_PROJECT_DIR."""
    if env := os.environ.get("ARIADNE_ROOT"):
        return Path(env)
    if gefunden := finde_lernrepo(Path.cwd()):
        return gefunden
    if (projekt := os.environ.get("CLAUDE_PROJECT_DIR")) and (Path(projekt) / MARKER).is_file():
        return Path(projekt)
    raise SystemExit("FEHLER: Kein Ariadne-Lern-Repo gefunden (keine ariadne.toml). Erst /ariadne:einrichten.")


def konfig() -> dict:
    try:
        pfad = wurzel() / MARKER
    except SystemExit:
        return {}
    return tomllib.loads(pfad.read_text()) if pfad.exists() else {}


def jetzt() -> datetime:
    if env := os.environ.get("ARIADNE_JETZT"):  # nur für Tests
        return datetime.fromisoformat(env)
    return datetime.now(timezone.utc).astimezone()


def heute() -> date:
    return jetzt().date()


def lies_json(pfad: Path, standard=None):
    if not pfad.exists():
        return standard
    return json.loads(pfad.read_text())


def schreib_json(pfad: Path, daten) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    tmp = pfad.with_suffix(pfad.suffix + ".tmp")
    tmp.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(pfad)


# ---------------------------------------------------------------- Sitzung

def sitzungs_id() -> str:
    """Die SessionStart-Hook schreibt die ID nach $CLAUDE_ENV_FILE und als Rückfall nach sitzungen/.aktuell."""
    if sid := os.environ.get("ARIADNE_SESSION"):
        return sid
    datei = wurzel() / "sitzungen" / ".aktuell"
    return datei.read_text().strip() if datei.exists() else "ohne-sitzung"


def sitzungs_ordner(tag: date | None = None) -> Path:
    ordner = wurzel() / "sitzungen" / (tag or heute()).isoformat()
    ordner.mkdir(parents=True, exist_ok=True)
    return ordner


def protokolliere(art: str, **daten) -> dict:
    """Hängt ein Ereignis an sitzungen/<tag>/protokoll.jsonl an."""
    eintrag = {"zeit": jetzt().isoformat(timespec="seconds"), "sitzung": sitzungs_id(), "art": art, **daten}
    with open(sitzungs_ordner() / "protokoll.jsonl", "a") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
    return eintrag


def protokoll(tage: int | None = None) -> list[dict]:
    """Alle Ereignisse, optional nur der letzten n Tage, zeitlich sortiert."""
    eintraege = []
    for datei in sorted((wurzel() / "sitzungen").glob("*/protokoll.jsonl")):
        if tage is not None:
            try:
                tag = date.fromisoformat(datei.parent.name)
            except ValueError:
                continue
            if (heute() - tag).days >= tage:
                continue
        for zeile in datei.read_text().splitlines():
            if zeile.strip():
                eintraege.append(json.loads(zeile))
    return sorted(eintraege, key=lambda e: e["zeit"])


# ---------------------------------------------------------------- Git

def commit(pfade: list[Path], nachricht: str) -> None:
    """Jede Änderung am Lernermodell wird ein Commit (Abschnitt 5.8). Ohne Git-Repo: still überspringen."""
    root = wurzel()
    if not (root / ".git").exists() or os.environ.get("ARIADNE_KEIN_GIT"):
        return
    rel = [str(p.relative_to(root)) for p in pfade if p.exists()]
    if not rel:
        return
    subprocess.run(["git", "add", "--", *rel], cwd=root, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", nachricht, "--", *rel],
        cwd=root, capture_output=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "Ariadne", "GIT_COMMITTER_NAME": "Ariadne",
             "GIT_AUTHOR_EMAIL": "ariadne@localhost", "GIT_COMMITTER_EMAIL": "ariadne@localhost"},
    )
