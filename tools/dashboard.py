"""Zeigt den Lernstand als Web-Dashboard und hält ihn aktuell, bis es beendet wird.
Aufruf: ariadne dashboard [--port N] [--no-open] [--einmal]
Rendert mit md-dashboard (github.com/juliantrude/markdown-dashboard). Liest nur; das Markdown liegt in
sitzungen/.dashboard/. Mit --einmal wird es nur geschrieben, ohne Server."""
import argparse
import shlex
import shutil
import signal
import subprocess
import sys
import threading
from pathlib import Path

from kern.basis import konfig, wurzel
from kern.dashboard import markdown
from kern.uebersicht import uebersicht

TAKT_S = 2.0


def werkzeug() -> list[str]:
    if befehl := konfig().get("dashboard", {}).get("befehl"):
        return shlex.split(befehl)
    if pfad := shutil.which("md-dashboard"):
        return [pfad]
    raise SystemExit("FEHLER: md-dashboard nicht gefunden. Installieren (siehe README) "
                     "oder in ariadne.toml unter [dashboard] als befehl eintragen.")


def schreibe(ziel: Path) -> None:
    text = markdown(uebersicht())
    if ziel.exists() and ziel.read_text() == text:
        return
    tmp = ziel.with_suffix(".tmp")
    tmp.write_text(text)
    tmp.replace(ziel)


def ordner() -> Path:
    o = wurzel() / "sitzungen" / ".dashboard"
    o.mkdir(parents=True, exist_ok=True)
    (o / ".gitignore").write_text("*\n")
    return o


def main() -> int:
    p = argparse.ArgumentParser(prog="dashboard.py")
    p.add_argument("--port", type=int, default=konfig().get("dashboard", {}).get("port", 4173))
    p.add_argument("--no-open", action="store_true")
    p.add_argument("--einmal", action="store_true")
    x = p.parse_args()

    ziel = ordner() / "lernstand.md"
    schreibe(ziel)
    if x.einmal:
        print(ziel)
        return 0

    befehl = [*werkzeug(), str(ziel), "--port", str(x.port), *(["--no-open"] if x.no_open else [])]
    server = subprocess.Popen(befehl)
    ende = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: ende.set())
    print(f"Dashboard: http://localhost:{x.port}", flush=True)
    try:
        while server.poll() is None and not ende.wait(TAKT_S):
            try:
                schreibe(ziel)
            except (OSError, ValueError, KeyError) as e:  # eine halb geschriebene Datei darf den Server nicht beenden
                print(f"Stand nicht lesbar: {e}", file=sys.stderr, flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        server.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
