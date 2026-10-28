"""Ebene ① der Quellenprüfung (Abschnitt 5.6): deterministisch, ohne Modell.

Zitat:  ⟦"wörtliches Zitat" | datei.pdf S. n⟧   (n = PDF-Seite, wie im Viewer gezählt)
Lauf:   ⟦lauf: r3⟧
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from kern.basis import lies_json, wurzel

ZITAT = re.compile(r'⟦\s*["„“](?P<q>.+?)["“”]\s*\|\s*(?P<f>[\w./ -]+?)\s+S\.\s*(?P<s>\d+)\s*⟧', re.S)
LAUF = re.compile(r"⟦\s*lauf:\s*(?P<r>r\d+)\s*⟧")
UNBELEGT = re.compile(r"⟦\s*unbelegt\s*⟧")
MIN_SEITENTEXT = 200


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", t)  # Silbentrennung am Zeilenende
    t = re.sub(r"[„“”«»″]", '"', t)
    t = re.sub(r"[‚‘’`´]", "'", t)
    t = re.sub(r"[‐‑‒–—]", "-", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def text_ordner() -> Path:
    return wurzel() / "material" / ".text"


def dokument(datei: str) -> str | None:
    """Findet den Textordner zu einer Dateiangabe: relativer Pfad unter material/ oder eindeutiger Dateiname."""
    index = lies_json(text_ordner() / "index.json", {"dokumente": {}})["dokumente"]
    datei = datei.strip()
    for slug, d in index.items():
        if d["pfad"] == datei:
            return slug
    treffer = [slug for slug, d in index.items() if Path(d["pfad"]).name == datei]
    return treffer[0] if len(treffer) == 1 else None


def seitentext(datei: str, seite: int) -> str | None:
    slug = dokument(datei)
    if slug is None:
        return None
    p = text_ordner() / slug / f"{seite:03d}.txt"
    return p.read_text() if p.exists() else None


def _seiten_anzahl(datei: str) -> int:
    slug = dokument(datei)
    if slug is None:
        return 0
    return lies_json(text_ordner() / "index.json")["dokumente"][slug]["seiten"]


def nachbarseite_mit_treffer(datei: str, seite: int, zitat_norm: str) -> int | None:
    for s in (seite - 1, seite + 1):
        t = seitentext(datei, s) if s >= 1 else None
        if t and zitat_norm in norm(t):
            return s
    # Zitat über einen Seitenumbruch: Ende von S. n mit Anfang von S. n+1
    a, b = seitentext(datei, seite), seitentext(datei, seite + 1)
    if a and b and zitat_norm in norm(a + "\n" + b):
        return seite
    return None


def pruefe_zitate(antwort: str) -> tuple[list[str], list[dict]]:
    """Liefert (Fehler, gefundene Zitate mit umgebendem Absatz für Ebene ②)."""
    fehler, zitate = [], []
    for m in ZITAT.finditer(antwort):
        datei, seite, q = m["f"].strip(), int(m["s"]), norm(m["q"])
        text = seitentext(datei, seite)
        if dokument(datei) is None:
            fehler.append(f'Dokument unbekannt: {datei} (nicht eingelesen oder Name mehrdeutig)')
        elif text is None or len(text.strip()) < MIN_SEITENTEXT:
            fehler.append(f"nicht prüfbar: {datei} S. {seite} (Seite leer, Scan oder Formelseite)")
        elif q in norm(text):
            zitate.append({"zitat": m["q"], "datei": datei, "seite": seite, "absatz": absatz(text, m["q"])})
        else:
            nachbar = nachbarseite_mit_treffer(datei, seite, q)
            if nachbar == seite:
                zitate.append({"zitat": m["q"], "datei": datei, "seite": seite, "absatz": m["q"]})
            elif nachbar:
                fehler.append(f'falsche Seite: "{m["q"][:60]}" steht auf S. {nachbar}, nicht S. {seite}')
            else:
                fehler.append(f'Zitat nicht gefunden: "{m["q"][:60]}" in {datei} S. {seite}')
    return fehler, zitate


def absatz(seitentext_roh: str, zitat: str, rand: int = 600) -> str:
    """Das Zitat mit umgebendem Kontext, damit der Prüfer sieht, ob es aus dem Zusammenhang gerissen ist."""
    t = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", seitentext_roh))
    pos = norm(t).find(norm(zitat))
    if pos < 0:
        return t[: 2 * rand]
    return t[max(0, pos - rand): pos + len(zitat) + rand]


def pruefe_laeufe(antwort: str, sitzung: str) -> list[str]:
    fehler = []
    for m in LAUF.finditer(antwort):
        laeufe = list((wurzel() / "sitzungen").glob(f"*/runs/{m['r']}.json"))
        eigene = [p for p in laeufe if (lies_json(p) or {}).get("sitzung") == sitzung]
        if not eigene:
            fehler.append(f"Lauf {m['r']} existiert in dieser Sitzung nicht")
    return fehler


def hat_belege(antwort: str) -> bool:
    return bool(ZITAT.search(antwort) or LAUF.search(antwort) or UNBELEGT.search(antwort))
