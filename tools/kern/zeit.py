"""Gemessene Lernzeit. Die UserPromptSubmit-Hook schreibt pro Eingabe einen Zeitstempel,
daraus wird aktive Zeit geschätzt: Abstände bis LUECKE zählen, längere Pausen nicht."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from kern.basis import heute, jetzt, sitzungs_ordner, wurzel

LUECKE = timedelta(minutes=15)
EINZEL = timedelta(minutes=2)  # eine einzelne Eingabe ohne Nachbarn


def melde_aktivitaet(sitzung: str) -> None:
    with open(sitzungs_ordner() / "aktivitaet.jsonl", "a") as f:
        f.write(json.dumps({"zeit": jetzt().isoformat(timespec="seconds"), "sitzung": sitzung}) + "\n")


def _stempel(von: date, bis: date) -> dict[str, list[datetime]]:
    pro_sitzung: dict[str, list[datetime]] = {}
    for datei in (wurzel() / "sitzungen").glob("*/aktivitaet.jsonl"):
        try:
            tag = date.fromisoformat(datei.parent.name)
        except ValueError:
            continue
        if not von <= tag <= bis:
            continue
        for zeile in datei.read_text().splitlines():
            if zeile.strip():
                e = json.loads(zeile)
                pro_sitzung.setdefault(e["sitzung"], []).append(datetime.fromisoformat(e["zeit"]))
    return pro_sitzung


def aktive_minuten(von: date, bis: date) -> float:
    gesamt = timedelta()
    for stempel in _stempel(von, bis).values():
        stempel.sort()
        gesamt += EINZEL
        for a, b in zip(stempel, stempel[1:]):
            gesamt += min(b - a, LUECKE) if b - a <= LUECKE else EINZEL
    return gesamt.total_seconds() / 60


def minuten_diese_woche() -> float:
    montag = heute() - timedelta(days=heute().weekday())
    return aktive_minuten(montag, heute())
