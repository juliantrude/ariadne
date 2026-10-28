import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HOOKS = REPO / "hooks"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Ein leeres Ariadne-Datenverzeichnis, feste Sitzung und feste Uhrzeit."""
    for d in ("learner/kapitel", "material/.text", "sitzungen", ".tutor/karten"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "ariadne.toml").write_text((REPO / "vorlage" / "ariadne.toml").read_text())
    monkeypatch.setenv("ARIADNE_ROOT", str(tmp_path))
    monkeypatch.setenv("ARIADNE_SESSION", "s1")
    monkeypatch.setenv("ARIADNE_JETZT", "2026-11-02T10:00:00+01:00")
    monkeypatch.setenv("ARIADNE_KEIN_GIT", "1")
    monkeypatch.setenv("ARIADNE_OHNE_PRUEFER", "1")
    for v in ("ARIADNE_PRUEFER", "ARIADNE_TRANSCRIPT", "CLAUDE_ENV_FILE", "CLAUDE_PROJECT_DIR"):
        monkeypatch.delenv(v, raising=False)
    return tmp_path


def seiten(repo: Path, pfad: str, texte: list[str]) -> None:
    """Legt Seitentexte an, als hätte ingest.py das PDF zerlegt."""
    slug = pfad.rsplit(".", 1)[0].replace("/", "-")
    ordner = repo / "material" / ".text" / slug
    ordner.mkdir(parents=True, exist_ok=True)
    for i, t in enumerate(texte, 1):
        (ordner / f"{i:03d}.txt").write_text(t)
    index_pfad = repo / "material" / ".text" / "index.json"
    index = json.loads(index_pfad.read_text()) if index_pfad.exists() else {"dokumente": {}}
    index["dokumente"][slug] = {"pfad": pfad, "seiten": len(texte), "leer": []}
    index_pfad.write_text(json.dumps(index))


def hook(name: str, ereignis: dict, **env) -> dict | None:
    r = subprocess.run([sys.executable, str(HOOKS / name)], input=json.dumps(ereignis), capture_output=True,
                       text=True, env={**os.environ, **env}, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout) if r.stdout.strip() else None


def transkript(pfad: Path, verlauf: list[tuple[str, str]]) -> Path:
    """Schreibt ein Transkript im Format von Claude Code 2.1 (siehe tests/fixtures/transkript_2_1.jsonl)."""
    zeilen = []
    for rolle, text in verlauf:
        if rolle == "user":
            zeilen.append({"type": "user", "message": {"role": "user", "content": text}, "isSidechain": False})
        else:
            zeilen.append({"type": "assistant", "message": {"role": "assistant",
                                                            "content": [{"type": "text", "text": text}]}})
    pfad.write_text("\n".join(json.dumps(z) for z in zeilen) + "\n")
    return pfad
