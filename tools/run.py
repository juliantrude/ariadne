"""Führt Code aus und protokolliert Ein- und Ausgabe, damit die Maschine widerlegt (P5).

  ariadne run vorhersage "Stride 4096 hat mehr Page Faults"   # vorher festhalten
  ariadne run stride.c                                         # kompilieren (gcc -O1) und ausführen
  ariadne run skript.py | skript.sh
  ariadne run -- perf stat -e dTLB-load-misses ./a.out         # beliebiger Befehl
Jeder Lauf landet in sitzungen/<tag>/runs/rN.json und wird mit ⟦lauf: rN⟧ belegt.
Keine Sandbox: Läufe haben die Rechte des Nutzers. Nur eigenen Code ausführen."""
import json
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from kern.basis import jetzt, lies_json, protokolliere, schreib_json, sitzungs_id, sitzungs_ordner

MAX_AUSGABE = 20_000


def vorhersage(text: str) -> str:
    ordner = sitzungs_ordner()
    pfad = ordner / "vorhersagen.json"
    alle = lies_json(pfad, [])
    vid = f"v{len(alle) + 1}"
    alle.append({"id": vid, "sitzung": sitzungs_id(), "zeit": jetzt().isoformat(timespec="seconds"),
                 "text": text, "lauf": None})
    schreib_json(pfad, alle)
    protokolliere("vorhersage", vorhersage=vid)
    return vid


def _offene_vorhersage(ordner: Path) -> dict | None:
    alle = lies_json(ordner / "vorhersagen.json", [])
    offen = [v for v in alle if v["sitzung"] == sitzungs_id() and v["lauf"] is None]
    return offen[-1] if offen else None


def befehl_fuer(args: list[str], tmp: Path) -> list[list[str]]:
    if len(args) == 1 and args[0].endswith(".c"):
        exe = tmp / "a.out"
        return [["gcc", "-O1", "-o", str(exe), args[0]], [str(exe)]]
    if len(args) >= 1 and args[0].endswith(".py"):
        return [[sys.executable, *args]]
    if len(args) >= 1 and args[0].endswith(".sh"):
        return [["bash", *args]]
    return [args]


def ausfuehren(args: list[str], timeout: int = 120) -> dict:
    ordner = sitzungs_ordner()
    runs = ordner / "runs"
    runs.mkdir(exist_ok=True)
    rid = f"r{len(list(runs.glob('r*.json'))) + 1}"
    schritte = []
    with tempfile.TemporaryDirectory() as tmp:
        for cmd in befehl_fuer(args, Path(tmp)):
            t0 = time.monotonic()
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                rc, out, err = r.returncode, r.stdout, r.stderr
            except subprocess.TimeoutExpired as e:
                rc, out, err = -1, (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""), f"Zeitüberschreitung nach {timeout} s"
            schritte.append({"befehl": shlex.join(cmd), "rc": rc, "stdout": out[-MAX_AUSGABE:],
                             "stderr": err[-MAX_AUSGABE:], "sekunden": round(time.monotonic() - t0, 3)})
            if rc != 0:
                break
    v = _offene_vorhersage(ordner)
    lauf = {"id": rid, "sitzung": sitzungs_id(), "zeit": jetzt().isoformat(timespec="seconds"),
            "eingabe": args, "schritte": schritte, "vorhersage": v}
    if args and Path(args[0]).is_file():
        lauf["quelltext"] = Path(args[0]).read_text(errors="replace")[:MAX_AUSGABE]
    schreib_json(runs / f"{rid}.json", lauf)
    if v:
        alle = lies_json(ordner / "vorhersagen.json", [])
        for x in alle:
            if x["id"] == v["id"]:
                x["lauf"] = rid
        schreib_json(ordner / "vorhersagen.json", alle)
    protokolliere("lauf", lauf=rid, vorhersage=v["id"] if v else None)
    return lauf


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__)
        return 1
    if argv[0] == "vorhersage":
        print(f"Vorhersage {vorhersage(' '.join(argv[1:]))} festgehalten. Jetzt ausführen.")
        return 0
    if argv[0] == "--":
        argv = argv[1:]
    lauf = ausfuehren(argv)
    for s in lauf["schritte"]:
        print(f"$ {s['befehl']}  (rc {s['rc']}, {s['sekunden']} s)")
        if s["stdout"]:
            print(s["stdout"].rstrip())
        if s["stderr"]:
            print(s["stderr"].rstrip())
    if lauf["vorhersage"]:
        print(f"Vorhersage {lauf['vorhersage']['id']} war: {lauf['vorhersage']['text']}")
    print(f"Beleg: ⟦lauf: {lauf['id']}⟧")
    return 0


if __name__ == "__main__":
    sys.exit(main())
