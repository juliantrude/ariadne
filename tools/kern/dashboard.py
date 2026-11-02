"""Schreibt den Lernstand als Markdown für md-dashboard. Jede ##-Überschrift wird dort eine Karte.
Nur Darstellung: Alle Zahlen kommen aus kern/uebersicht.py."""
from __future__ import annotations

import json

STUFEN_LEGENDE = "Stufe 0 unbekannt, 4 sicher, ab {ziel} sitzt es."


def _zelle(text: str) -> str:
    return text.replace("|", "/")


def _chart(typ: str, kategorien: list[str], reihen: list[tuple[str, list]]) -> str:
    daten = {"type": typ, "categories": kategorien,
             "series": [{"label": name, "data": werte} for name, werte in reihen]}
    return f"```chart\n{json.dumps(daten, ensure_ascii=False)}\n```"


def _matrix(titel: str, zeilen: list[dict], ziel: int) -> list[str]:
    stufen = range(len(zeilen[0]["stufen"]))
    reihen = [(str(b), [z["stufen"][b] for z in zeilen]) for b in stufen]
    return [f"## {titel}", "", _chart("heatmap", [z["name"] for z in zeilen], reihen), "",
            STUFEN_LEGENDE.format(ziel=ziel), ""]


def _kennzahlen(u: dict) -> list[str]:
    k, s = u["koennen"], u["statistik"]
    return ["## Überblick", "", k["fazit"], "", f"- Konzepte: {k['gesamt']}", f"- Sitzen: {k['sitzen']}",
            f"- Wackeln: {k['wackeln']}", f"- Fällig: {u['wiederholung']['faellig']}",
            f"- Fehlvorstellungen: {sum(z['fehlvorstellungen'] for z in k['bereiche'])}",
            f"- Lernzeit 14 Tage (min): {s['lernzeit_min']}", ""]


def _baustellen(k: dict) -> list[str]:
    zeilen = k["bereiche"]
    return ["## Baustellen je Bereich", "",
            _chart("bar-stacked", [z["name"] for z in zeilen],
                   [("Fällig", [z["faellig"] for z in zeilen]),
                    ("Fehlvorstellungen", [z["fehlvorstellungen"] for z in zeilen])]), ""]


def _schwaechen(k: dict) -> list[str]:
    raus = ["## Zuerst angehen", "", "| Konzept | Warum | Starten mit |", "|---|---|---|",
            *(f"| {_zelle(w['titel'])} | {w['grund']} | `{w['befehl']}` |" for w in k["schwaechen"])]
    if k["weitere_schwaechen"]:
        raus += ["", f"Und {k['weitere_schwaechen']} weitere."]
    return raus + [""]


def _einschaetzung(s: dict) -> list[str]:
    hoch, niedrig = s["kalibrierung"]["hoch"], s["kalibrierung"]["niedrig"]
    return ["## Selbsteinschätzung, 14 Tage", "",
            _chart("bar-stacked", ["sehr sicher (4 bis 5)", "unsicher (1 bis 2)"],
                   [("richtig", [hoch["richtig"], niedrig["richtig"]]),
                    ("falsch", [hoch["gesamt"] - hoch["richtig"], niedrig["gesamt"] - niedrig["richtig"]])]), "",
            f"{s['abrufe']['richtig']} von {s['abrufe']['gesamt']} Abrufen richtig.", ""]


def _lernzeit(s: dict) -> list[str]:
    tage = s["lernzeit_tage"]
    return ["## Lernzeit, 14 Tage", "",
            _chart("bar", [t["datum"][5:] for t in tage], [("Minuten", [t["minuten"] for t in tage])]), "",
            f"{s['lernzeit_min']} Minuten an {s['lerntage']} {'Lerntag' if s['lerntage'] == 1 else 'Lerntagen'}.", ""]


def _hinweise(s: dict) -> list[str]:
    h = s["hinweise"]
    schnitt = "keine Hinweise" if h["schnitt"] is None else f"im Schnitt Stufe {h['schnitt']}"
    return ["## Hinweise, 14 Tage", "", f"{h['anzahl']} gemeldete Hinweisstufen, {schnitt}.", "",
            f"- Stufe 4: {h['stufe_4']}", f"- Notausgang: {h['notausgang']}", ""]


def _plan(k: dict) -> list[str]:
    raus = [f"## Plan: {k['titel']}", ""]
    if k.get("fehler"):
        return raus + [f"Nicht lesbar: {k['fehler']}", ""]
    plan = k.get("plan")
    if plan:
        raus += [f"Plan v{plan['version']} ({plan['status']}), Rückstand {plan['rueckstand_tage']} Tage, "
                 f"Woche {plan['lernzeit_woche_min']} von {plan['vereinbart_woche_min']} min. "
                 f"Nächster Schritt: `{k['naechster_schritt']}`", ""]
        raus += [f"- [{'x' if m['zustand'] == 'bestanden' else ' '}] {m['id']} {m['zieldatum']} {m['titel']} "
                 f"({m['konzepte_sitzen']})" for m in plan["meilensteine"]]
        raus += ["", *(f"> Neu verhandeln: {g}" for g in plan["neuverhandeln"])]
    else:
        raus += [f"Noch kein Plan. Nächster Schritt: `{k['naechster_schritt']}`"]
    return raus + [""]


def _termine(deadlines: list[dict]) -> list[str]:
    def wann(t: int) -> str:
        return "heute" if t == 0 else f"vor {-t} Tagen" if t < 0 else f"in {t} Tagen"

    if not deadlines:
        return ["## Termine", "", "Keine Termine.", ""]
    return ["## Termine", "", "| Datum | Wann | Was |", "|---|---|---|",
            *(f"| {d['datum']} | {'verpasst' if d['zustand'] == 'verpasst' else wann(d['tage'])} "
              f"| {_zelle(d['kapitel'])}: {_zelle(d['titel'])} |" for d in deadlines), ""]


def _aktionen(u: dict) -> list[str]:
    return ["## Nächste Schritte", "", "| Was | In Claude Code eingeben |", "|---|---|",
            *(f"| {_zelle(a['titel'])} | `{a['befehl']}` |" for a in u["aktionen"]), ""]


def markdown(u: dict) -> str:
    k, s = u["koennen"], u["statistik"]
    raus = ["# Ariadne: Lernstand", "", *_kennzahlen(u)]
    if k["kapitel"]:
        raus += _matrix("Beherrschung je Kapitel", k["kapitel"], k["ziel"])
    if k["bereiche"]:
        raus += _matrix("Beherrschung je Bereich", k["bereiche"], k["ziel"])
        raus += _baustellen(k)
    if k["schwaechen"]:
        raus += _schwaechen(k)
    for kapitel in u["kapitel"]:
        raus += _plan(kapitel)
    raus += _termine(u["deadlines"])
    raus += _lernzeit(s) + _einschaetzung(s) + _hinweise(s) + _aktionen(u)
    return "\n".join(raus)
