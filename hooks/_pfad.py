"""Gemeinsamer Vorspann der Hooks: tools/ importierbar machen und nur in Lern-Repos aktiv werden."""
import json
import os
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "tools"))

from kern.basis import MARKER, finde_lernrepo  # noqa: E402


def _lernrepo() -> Path | None:
    if env := os.environ.get("ARIADNE_ROOT"):
        return Path(env) if (Path(env) / MARKER).is_file() else None
    start = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    return finde_lernrepo(start)


DATEN = _lernrepo()
if DATEN is not None:
    os.environ["ARIADNE_ROOT"] = str(DATEN)


def aus() -> bool:
    """Kein Lern-Repo (das Plugin ist überall installiert, wirkt aber nur dort)
    oder Prüfaufruf (Rekursionsschutz, T11)."""
    return DATEN is None or bool(os.environ.get("ARIADNE_PRUEFER"))


def ereignis() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
