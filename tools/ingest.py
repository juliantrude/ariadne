"""Zerlegt ein PDF in Seitentexte für die Quellenprüfung.
Aufruf: ariadne ingest material/os/skript.pdf
Ergebnis: material/.text/<slug>/001.txt ... und ein Eintrag in material/.text/index.json.
Seitenzahl = PDF-Seite, wie im Viewer gezählt (nicht die gedruckte Seitenzahl)."""
import os
import subprocess
import sys
from pathlib import Path

from kern.basis import jetzt, lies_json, schreib_json, wurzel
from kern.quellen import MIN_SEITENTEXT, text_ordner


def slug_fuer(rel: Path) -> str:
    return str(rel.with_suffix("")).replace("/", "-")


def einlesen(pdf: Path) -> dict:
    # Links nicht auflösen: material/<feld> darf auf einen Ordner außerhalb des Repos zeigen.
    pdf = Path(os.path.abspath(pdf))
    material = Path(os.path.abspath(wurzel() / "material"))
    try:
        rel = pdf.relative_to(material)
    except ValueError:
        raise SystemExit(f"FEHLER: {pdf} liegt nicht unter material/. Erst dorthin kopieren.")
    r = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FEHLER: pdftotext: {r.stderr.strip()}")
    seiten = r.stdout.split("\f")
    if seiten and not seiten[-1].strip():
        seiten = seiten[:-1]
    slug = slug_fuer(rel)
    ziel = text_ordner() / slug
    ziel.mkdir(parents=True, exist_ok=True)
    for alt in ziel.glob("*.txt"):
        alt.unlink()
    leer = []
    for i, text in enumerate(seiten, 1):
        (ziel / f"{i:03d}.txt").write_text(text)
        if len(text.strip()) < MIN_SEITENTEXT:
            leer.append(i)
    index_pfad = text_ordner() / "index.json"
    index = lies_json(index_pfad, {"dokumente": {}})
    index["dokumente"][slug] = {"pfad": str(rel), "seiten": len(seiten), "leer": leer,
                                "eingelesen": jetzt().isoformat(timespec="seconds")}
    schreib_json(index_pfad, index)
    return index["dokumente"][slug]


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        d = einlesen(Path(arg))
        print(f"{d['pfad']}: {d['seiten']} Seiten, nicht prüfbar (leer/Scan/Formel): {d['leer'] or 'keine'}")
