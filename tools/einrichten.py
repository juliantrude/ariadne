"""Legt ein neues Lern-Repo an: Daten getrennt vom Plugin-Code.
Aufruf: ariadne einrichten <verzeichnis>
Vorhandene Dateien werden nie überschrieben."""
import shutil
import subprocess
import sys
from pathlib import Path

VORLAGE = Path(__file__).resolve().parents[1] / "vorlage"
ORDNER = ["learner/kapitel", "material", ".tutor/karten", "sitzungen"]


def einrichten(ziel: Path) -> list[str]:
    ziel = ziel.expanduser().resolve()
    if (ziel / "ariadne.toml").exists():
        raise SystemExit(f"FEHLER: {ziel} ist bereits ein Lern-Repo.")
    ziel.mkdir(parents=True, exist_ok=True)
    angelegt = []
    for quelle in sorted(VORLAGE.rglob("*")):
        if quelle.is_file():
            dateiziel = ziel / quelle.relative_to(VORLAGE)
            if dateiziel.exists():
                continue
            dateiziel.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(quelle, dateiziel)
            angelegt.append(str(dateiziel.relative_to(ziel)))
    for o in ORDNER:
        (ziel / o).mkdir(parents=True, exist_ok=True)
        (ziel / o / ".gitkeep").touch()
    if not (ziel / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=ziel, check=True)
        subprocess.run(["git", "add", "."], cwd=ziel, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "Ariadne-Lern-Repo eingerichtet"], cwd=ziel, capture_output=True)
    return angelegt


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    neu = einrichten(Path(sys.argv[1]))
    print(f"Lern-Repo bereit: {Path(sys.argv[1]).expanduser().resolve()}")
    print(f"Angelegt: {', '.join(neu) or '(nichts, alles war schon da)'}")
    print("Weiter: dort `claude` starten, dann /ariadne:einlesen und /ariadne:kapitel.")
