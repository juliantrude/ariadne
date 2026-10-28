"""Kapitel, Lehrplan, Meilensteine und Fortschritt.

Arbeitsteilung wie überall in Ariadne: Das Modell schlägt die didaktische Gliederung
vor (welche Konzepte bilden einen Meilenstein, welche Prüfung passt), und verhandelt
mit dem Lernenden. Alles, was Zahl ist – Aufwand, Termine, Machbarkeit, Bestehen,
Rückstand –, rechnet dieser Code. So kann sich kein Plan schönrechnen.
"""
from __future__ import annotations

import math
import os
from datetime import date, timedelta

from kern import lernermodell as lm
from kern.basis import commit, heute, jetzt, konfig, lies_json, protokolliere, schreib_json, wurzel
from kern.quellen import norm
from kern.transkript import nutzer_eingaben
from kern.zeit import aktive_minuten

ENERGIE = ("niedrig", "mittel", "hoch")
PRUEFUNGSARTEN = ("zwischenpruefung", "challenge")
ERGEBNIS_PUNKTE = {"richtig": 1.0, "teilweise": 0.5, "falsch": 0.0}


class Fehler(Exception):
    pass


def _cfg(abschnitt: str) -> dict:
    standard = {
        "plan": {"aufwand_min": [90, 60, 35, 15, 0], "wiederholung_zuschlag": 0.2, "puffer": 0.15,
                 "pruefung_min": 30, "neue_pro_sitzung": {"niedrig": 1, "mittel": 2, "hoch": 3},
                 "neuverhandeln_ab_tagen": 7},
        "meilenstein": {"schwelle": 0.8, "ziel_beherrschung": 3},
    }[abschnitt]
    return {**standard, **konfig().get(abschnitt, {})}


def pfad(kid: str):
    return wurzel() / "learner" / "kapitel" / f"{kid}.json"


def lade(kid: str) -> dict:
    daten = lies_json(pfad(kid))
    if daten is None:
        raise Fehler(f"Kapitel {kid} existiert nicht. Erst mit 'ariadne plan neu' anlegen.")
    return daten


def alle() -> list[dict]:
    return [lies_json(p) for p in sorted((wurzel() / "learner" / "kapitel").glob("*.json"))]


def speichere(kap: dict, nachricht: str) -> None:
    schreib_json(pfad(kap["id"]), kap)
    commit([pfad(kap["id"]), lm.konzepte_pfad(), lm.kalibrierung_pfad()], f"plan: {kap['id']} {nachricht}")


# ---------------------------------------------------------------- Kapitel anlegen

def neu(kid: str, titel: str, konzepte: list[str], ziel_art: str, ziel_datum: str | None,
        ziel_beschreibung: str = "", stichworte: list[str] | None = None) -> dict:
    if pfad(kid).exists():
        raise Fehler(f"Kapitel {kid} existiert bereits.")
    bekannt = lm.lade()
    ids: list[str] = []
    for eintrag in konzepte:
        if eintrag.endswith(".") or eintrag.endswith("*"):
            treffer = sorted(k for k in bekannt if k.startswith(eintrag.rstrip("*")))
            if not treffer:
                raise Fehler(f"Kein Konzept beginnt mit {eintrag}.")
            ids += treffer
        elif eintrag in bekannt:
            ids.append(eintrag)
        else:
            raise Fehler(f"Unbekanntes Konzept {eintrag}. Erst /ariadne:einlesen oder 'ariadne lm anlegen'.")
    if not ids:
        raise Fehler("Ein Kapitel braucht mindestens ein Konzept.")
    if ziel_datum:
        date.fromisoformat(ziel_datum)
    kap = {
        "id": kid, "titel": titel, "angelegt": heute().isoformat(),
        "ziel": {"art": ziel_art, "datum": ziel_datum, "beschreibung": ziel_beschreibung},
        "konzepte": list(dict.fromkeys(ids)), "stichworte": stichworte or [],
        "vorwissen": {"status": "offen"}, "plan": None, "plan_historie": [], "pruefungen_laufend": {},
    }
    speichere(kap, "angelegt")
    protokolliere("kapitel_neu", kapitel=kid, konzepte=len(kap["konzepte"]))
    return kap


def vorwissen_abschliessen(kid: str, zusammenfassung: str, gedaechtnis: list[str]) -> dict:
    kap = lade(kid)
    konzepte = lm.lade()
    ohne = [k for k in kap["konzepte"] if "vorwissen" not in konzepte[k] and not konzepte[k]["historie"]]
    kap["vorwissen"] = {
        "status": "erledigt", "datum": heute().isoformat(), "zusammenfassung": zusammenfassung,
        "gedaechtnis_genutzt": gedaechtnis, "ohne_diagnose": ohne,
        "start_beherrschung": {k: konzepte[k]["beherrschung"] for k in kap["konzepte"]},
    }
    speichere(kap, "Vorwissensanalyse abgeschlossen")
    protokolliere("vorwissen_fertig", kapitel=kid, ohne_diagnose=len(ohne))
    return kap


# ---------------------------------------------------------------- Lehrplan

def _topologisch(ids: list[str], konzepte: dict) -> list[str]:
    drin, raus, besucht = set(ids), [], set()

    def besuche(k: str, pfad: tuple = ()):
        if k in pfad:
            raise Fehler(f"Zyklus in den Voraussetzungen: {' -> '.join(pfad + (k,))}")
        if k in besucht:
            return
        for v in konzepte[k]["voraussetzungen"]:
            if v in drin:
                besuche(v, pfad + (k,))
        besucht.add(k)
        raus.append(k)

    for k in ids:
        besuche(k)
    return raus


def _auto_gliederung(reihenfolge: list[str], konzepte: dict, groesse: int = 4) -> list[dict]:
    gruppen = [reihenfolge[i:i + groesse] for i in range(0, len(reihenfolge), groesse)]
    return [{"titel": " · ".join(konzepte[k]["titel"] for k in g[:2]) + (" …" if len(g) > 2 else ""),
             "konzepte": g, "pruefung": {"art": "zwischenpruefung",
                                         "beschreibung": "Gemischter Abruf ohne Hilfe zu allen Konzepten"}}
            for g in gruppen]


def _pruefe_pruefung(pruefung: dict, wo: str) -> None:
    art = pruefung.get("art", "zwischenpruefung")
    if art not in PRUEFUNGSARTEN:
        raise Fehler(f"{wo}: Prüfungsart muss eins von {PRUEFUNGSARTEN} sein.")
    if art == "challenge" and not pruefung.get("kriterien"):
        raise Fehler(f"{wo}: Eine Challenge braucht messbare 'kriterien'.")


def _pruefe_gliederung(gliederung: list[dict], offen: list[str], konzepte: dict) -> None:
    gesehen: list[str] = []
    for i, m in enumerate(gliederung, 1):
        if not m.get("konzepte"):
            raise Fehler(f"Meilenstein {i} hat keine Konzepte.")
        if i == 1:  # nur der nächste Meilenstein ist scharf, spätere liegen im Nebel
            _pruefe_pruefung(m.get("pruefung", {}), f"Meilenstein {i}")
        for k in m["konzepte"]:
            if k not in offen:
                raise Fehler(f"Meilenstein {i}: {k} gehört nicht zu den offenen Konzepten des Kapitels.")
            if k in gesehen:
                raise Fehler(f"{k} steht in mehreren Meilensteinen.")
            for v in konzepte[k]["voraussetzungen"]:
                if v in offen and v not in gesehen and v not in m["konzepte"]:
                    raise Fehler(f"{k} braucht {v}, das erst in einem späteren Meilenstein kommt.")
        gesehen += m["konzepte"]
    fehlt = [k for k in offen if k not in gesehen]
    if fehlt:
        raise Fehler(f"Diese Konzepte fehlen in der Gliederung: {', '.join(fehlt)}")


def _aufwand(kid_konzept: str, konzepte: dict, cfg: dict) -> float:
    b = min(konzepte[kid_konzept]["beherrschung"], len(cfg["aufwand_min"]) - 1)
    return cfg["aufwand_min"][b] * (1 + cfg["wiederholung_zuschlag"])


def vorschlag(kid: str, stunden_pro_woche: float, sitzungen_pro_woche: int, energie: str,
              gliederung: list[dict] | None = None, start: str | None = None, notiz: str = "") -> dict:
    """Berechnet einen Planentwurf. Bestandene Meilensteine bleiben bei einer Neuverhandlung erhalten."""
    if energie not in ENERGIE:
        raise Fehler(f"Energie muss eins von {ENERGIE} sein.")
    if stunden_pro_woche <= 0 or sitzungen_pro_woche <= 0:
        raise Fehler("Stunden und Sitzungen pro Woche müssen positiv sein.")
    kap = lade(kid)
    if kap["vorwissen"]["status"] != "erledigt":
        raise Fehler("Erst die Vorwissensanalyse abschließen (/ariadne:vorwissen). Ohne sie wäre jede Schätzung geraten.")
    cfg = _cfg("plan")
    konzepte = lm.lade()
    alt = kap["plan"]
    behalten = [m for m in (alt or {}).get("meilensteine", []) if m["status"] == "bestanden"]
    erledigt = {k for m in behalten for k in m["konzepte"]}
    offen = _topologisch([k for k in kap["konzepte"] if k not in erledigt], konzepte)
    gliederung = gliederung or _auto_gliederung(offen, konzepte)
    _pruefe_gliederung(gliederung, offen, konzepte)

    start_d = date.fromisoformat(start) if start else heute()
    pro_tag = stunden_pro_woche * 60 / 7
    neue_pro_woche = sitzungen_pro_woche * cfg["neue_pro_sitzung"][energie]
    naechste_nr = max([int(m["id"][1:]) for m in behalten], default=0) + 1
    version = (alt or {}).get("version", 0) + 1

    meilensteine, kum_min, kum_neu = [], 0.0, 0
    for i, g in enumerate(gliederung):
        minuten = sum(_aufwand(k, konzepte, cfg) for k in g["konzepte"]) + cfg["pruefung_min"]
        minuten *= 1 + cfg["puffer"]
        kum_min += minuten
        kum_neu += sum(1 for k in g["konzepte"] if konzepte[k]["beherrschung"] < 2)
        # Zwei Grenzen: verfügbare Zeit und wie viel Neues pro Woche verkraftbar ist.
        tage = max(kum_min / pro_tag, kum_neu / neue_pro_woche * 7)
        schwelle = _cfg("meilenstein")["schwelle"]
        if i == 0:
            pruefung = {"art": "zwischenpruefung", "schwelle": schwelle, **g.get("pruefung", {})}
        else:  # Nebel: Konzepte und Termin stehen, die Prüfung wird nach dem vorigen Meilenstein geschärft
            pruefung = {"art": "nebel", "schwelle": schwelle,
                        "skizze": g.get("pruefung", {}).get("beschreibung", "")}
        meilensteine.append({
            "id": f"M{naechste_nr + i}", "plan_version": version, "titel": g["titel"], "konzepte": g["konzepte"],
            "scharf": i == 0, "pruefung": pruefung, "minuten": round(minuten), "minuten_kum": round(kum_min),
            "zieldatum": (start_d + timedelta(days=math.ceil(tage))).isoformat(),
            "status": "offen", "versuche": [],
        })

    ende = date.fromisoformat(meilensteine[-1]["zieldatum"])
    machbar = _machbarkeit(kap, kum_min, ende, start_d, stunden_pro_woche, meilensteine)
    plan = {
        "version": version, "status": "entwurf", "erstellt": jetzt().isoformat(timespec="seconds"),
        "start": start_d.isoformat(), "ende": ende.isoformat(), "minuten_gesamt": round(kum_min),
        "ist_basis": round(_ist_anteil(kap, konzepte), 3) if behalten or alt else 0.0,
        "budget": {"stunden_pro_woche": stunden_pro_woche, "sitzungen_pro_woche": sitzungen_pro_woche,
                   "sitzung_min": round(stunden_pro_woche * 60 / sitzungen_pro_woche), "energie": energie,
                   "neue_pro_sitzung": cfg["neue_pro_sitzung"][energie]},
        "meilensteine": behalten + meilensteine, "machbarkeit": machbar, "notiz": notiz,
    }
    if alt and alt["status"] == "vereinbart":
        kap["plan_historie"].append(alt)
    kap["plan"] = plan
    speichere(kap, f"Planentwurf v{plan['version']}")
    protokolliere("plan_entwurf", kapitel=kid, version=plan["version"], machbar=machbar["machbar"])
    return kap


def _machbarkeit(kap: dict, minuten: float, ende: date, start: date, h_woche: float, ms: list[dict]) -> dict:
    ziel = kap["ziel"]["datum"]
    if not ziel:
        return {"machbar": True, "grund": "Kein Zieldatum gesetzt."}
    ziel_d = date.fromisoformat(ziel)
    wochen = max((ziel_d - start).days, 1) / 7
    verfuegbar = h_woche * 60 * wochen
    if ende <= ziel_d:
        return {"machbar": True, "reserve_tage": (ziel_d - ende).days, "verfuegbar_min": round(verfuegbar)}
    passt = [m["id"] for m in ms if date.fromisoformat(m["zieldatum"]) <= ziel_d]
    return {
        "machbar": False, "fehlende_tage": (ende - ziel_d).days,
        "verfuegbar_min": round(verfuegbar), "benoetigt_min": round(minuten),
        "noetige_stunden_pro_woche": round(minuten / 60 / wochen, 1),
        "passt_bis_ziel": passt,
        "hinweis": "Grenze kann auch die Zahl neuer Konzepte pro Woche sein (Energie, Sitzungen), nicht nur die Zeit.",
    }


def vereinbaren(kid: str, zustimmung: str) -> dict:
    """Macht den Entwurf verbindlich. 'zustimmung' ist der wörtliche Satz des Lernenden;
    die Stop-Hook prüft, dass er so im Gespräch steht."""
    kap = lade(kid)
    if not kap["plan"]:
        raise Fehler("Es gibt keinen Planentwurf.")
    if kap["plan"]["status"] == "vereinbart":
        raise Fehler("Der Plan ist bereits vereinbart. Änderungen gehen über einen neuen Vorschlag.")
    if len(zustimmung.strip()) < 2:
        raise Fehler("Die Zustimmung muss der wörtliche Satz des Lernenden sein.")
    if transcript := os.environ.get("ARIADNE_TRANSCRIPT"):
        if not any(norm(zustimmung) in norm(t) for t in nutzer_eingaben(transcript)):
            raise Fehler("Diese Zustimmung steht so nicht in den Eingaben des Lernenden. "
                         "Erst ausdrücklich fragen, dann den Satz wörtlich übernehmen.")
    kap["plan"].update(status="vereinbart", vereinbart=jetzt().isoformat(timespec="seconds"), zustimmung=zustimmung)
    speichere(kap, f"Plan v{kap['plan']['version']} vereinbart")
    protokolliere("plan_vereinbart", kapitel=kid, version=kap["plan"]["version"], zustimmung=zustimmung)
    return kap


def zuruecknehmen(kid: str) -> dict:
    """Setzt einen fälschlich vereinbarten Plan zurück auf Entwurf."""
    kap = lade(kid)
    if not kap["plan"] or kap["plan"]["status"] != "vereinbart":
        raise Fehler("Kein vereinbarter Plan zum Zurücknehmen.")
    kap["plan"]["status"] = "entwurf"
    for feld in ("vereinbart", "zustimmung"):
        kap["plan"].pop(feld, None)
    speichere(kap, f"Plan v{kap['plan']['version']} zurückgenommen")
    protokolliere("plan_zurueckgenommen", kapitel=kid, version=kap["plan"]["version"])
    return kap


# ---------------------------------------------------------------- Meilensteinprüfung

def _meilenstein(kap: dict, mid: str) -> dict:
    if not kap["plan"] or kap["plan"]["status"] != "vereinbart":
        raise Fehler("Meilensteinprüfungen gibt es erst mit einem vereinbarten Plan.")
    for m in kap["plan"]["meilensteine"]:
        if m["id"] == mid:
            return m
    raise Fehler(f"Meilenstein {mid} gibt es nicht.")


def schaerfen(kid: str, mid: str, pruefung: dict, titel: str | None = None) -> dict:
    """Legt die Prüfung eines Nebel-Meilensteins fest, sobald alle vorigen bestanden sind.
    Konzepte und Termine bleiben; wer die ändern will, verhandelt neu (vorschlag)."""
    kap = lade(kid)
    m = _meilenstein(kap, mid)
    if m.get("scharf", True):
        raise Fehler(f"{mid} ist bereits scharf.")
    davor = kap["plan"]["meilensteine"][:kap["plan"]["meilensteine"].index(m)]
    offen = [x["id"] for x in davor if x["status"] != "bestanden"]
    if offen:
        raise Fehler(f"Erst {', '.join(offen)} bestehen. Danach weiß man, was {mid} prüfen muss.")
    _pruefe_pruefung(pruefung, mid)
    m["pruefung"] = {"art": "zwischenpruefung", "schwelle": m["pruefung"].get("schwelle"), **pruefung}
    m["scharf"] = True
    if titel:
        m["titel"] = titel
    speichere(kap, f"{mid} geschärft ({m['pruefung']['art']})")
    protokolliere("meilenstein_geschaerft", kapitel=kid, meilenstein=mid, pruefungsart=m["pruefung"]["art"])
    return m


def pruefung_start(kid: str, mid: str) -> dict:
    kap = lade(kid)
    m = _meilenstein(kap, mid)
    if m["status"] == "bestanden":
        raise Fehler(f"{mid} ist schon bestanden.")
    if not m.get("scharf", True):
        raise Fehler(f"{mid} liegt noch im Nebel. Erst die Prüfung mit 'ariadne plan schaerfen' festlegen.")
    kap["pruefungen_laufend"][mid] = {"start": jetzt().isoformat(timespec="seconds"), "items": []}
    speichere(kap, f"{mid} Prüfung gestartet")
    protokolliere("pruefung_start", kapitel=kid, meilenstein=mid)
    return m


def pruefung_item(kid: str, mid: str, ergebnis: str, sicherheit: int,
                  konzept: str = "", kriterium: str = "") -> dict:
    """Ein Item: bei einer Zwischenprüfung eine Abruffrage zu einem Konzept,
    bei einer Challenge ein Kriterium. Abruffragen zählen zugleich als Abruf ohne Hilfe."""
    if ergebnis not in ERGEBNIS_PUNKTE:
        raise Fehler(f"Ergebnis muss eins von {sorted(ERGEBNIS_PUNKTE)} sein.")
    kap = lade(kid)
    m = _meilenstein(kap, mid)
    laufend = kap["pruefungen_laufend"].get(mid)
    if laufend is None:
        raise Fehler(f"Für {mid} läuft keine Prüfung. Erst 'ariadne plan pruefung-start'.")
    if m["pruefung"]["art"] == "challenge":
        if kriterium not in m["pruefung"]["kriterien"]:
            raise Fehler(f"Unbekanntes Kriterium. Erlaubt: {m['pruefung']['kriterien']}")
    elif konzept not in m["konzepte"]:
        raise Fehler(f"{konzept} gehört nicht zu {mid}.")
    laufend["items"].append({"konzept": konzept, "kriterium": kriterium, "ergebnis": ergebnis, "sicherheit": sicherheit})
    speichere(kap, f"{mid} Item {konzept or kriterium}: {ergebnis}")
    if konzept:
        lm.abruf(konzept, richtig=ergebnis == "richtig", sicherheit=sicherheit, stufe=0,
                 erklaerung_traegt=ergebnis == "richtig", quelle=f"meilenstein:{kid}:{mid}")
    return laufend


def pruefung_auswerten(kid: str, mid: str) -> dict:
    kap = lade(kid)
    m = _meilenstein(kap, mid)
    laufend = kap["pruefungen_laufend"].pop(mid, None)
    if not laufend or not laufend["items"]:
        raise Fehler(f"Für {mid} liegen keine Items vor.")
    items = laufend["items"]
    if m["pruefung"]["art"] == "challenge":
        fehlt = set(m["pruefung"]["kriterien"]) - {i["kriterium"] for i in items}
    else:
        fehlt = set(m["konzepte"]) - {i["konzept"] for i in items}
    if fehlt:
        kap["pruefungen_laufend"][mid] = laufend
        raise Fehler(f"Noch nicht geprüft: {', '.join(sorted(fehlt))}. Jedes Konzept bzw. Kriterium braucht ein Item.")
    quote = sum(ERGEBNIS_PUNKTE[i["ergebnis"]] for i in items) / len(items)
    schwache = sorted({i["konzept"] or i["kriterium"] for i in items if i["ergebnis"] != "richtig"})
    bestanden = quote >= m["pruefung"].get("schwelle", _cfg("meilenstein")["schwelle"])
    versuch = {"datum": heute().isoformat(), "quote": round(quote, 3), "bestanden": bestanden,
               "items": items, "schwache": schwache}
    m["versuche"].append(versuch)
    if bestanden:
        m["status"] = "bestanden"
        m["bestanden_am"] = heute().isoformat()
    speichere(kap, f"{mid} {'bestanden' if bestanden else 'nicht bestanden'} ({quote:.0%})")
    protokolliere("pruefung_ergebnis", kapitel=kid, meilenstein=mid, quote=round(quote, 3), bestanden=bestanden)
    return versuch


# ---------------------------------------------------------------- Fortschritt

def _soll_anteil(plan: dict, tag: date) -> float:
    """Geplanter Anteil der Gesamtarbeit, der an 'tag' erledigt sein sollte (linear je Meilenstein).
    Nach einer Neuverhandlung zählt der Stand bei Planbeginn als Basis, geplant wird nur der Rest."""
    basis = plan.get("ist_basis", 0.0)
    neu = [m for m in plan["meilensteine"] if m.get("plan_version") == plan["version"]]
    gesamt = neu[-1]["minuten_kum"] if neu else 0
    if not gesamt:
        return 1.0
    vorher_d, vorher_min = date.fromisoformat(plan["start"]), 0.0
    for m in neu:
        ziel_d, ziel_min = date.fromisoformat(m["zieldatum"]), m["minuten_kum"]
        if tag <= ziel_d:
            spanne = max((ziel_d - vorher_d).days, 1)
            anteil = min(max((tag - vorher_d).days / spanne, 0), 1)
            return basis + (1 - basis) * (vorher_min + anteil * (ziel_min - vorher_min)) / gesamt
        vorher_d, vorher_min = ziel_d, ziel_min
    return 1.0


def _ist_anteil(kap: dict, konzepte: dict) -> float:
    """Erledigter Anteil, gewichtet mit dem geschätzten Aufwand zum Startzeitpunkt."""
    cfg, ziel = _cfg("plan"), _cfg("meilenstein")["ziel_beherrschung"]
    start = kap["vorwissen"].get("start_beherrschung", {})
    summe = gewicht = 0.0
    for k in kap["konzepte"]:
        s = start.get(k, 0)
        w = cfg["aufwand_min"][min(s, len(cfg["aufwand_min"]) - 1)] or 1
        jetzt_b = konzepte[k]["beherrschung"]
        erledigt = 1.0 if s >= ziel else min(max((jetzt_b - s) / (ziel - s), 0), 1)
        summe += w * erledigt
        gewicht += w
    return summe / gewicht if gewicht else 1.0


def status(kid: str) -> dict:
    kap = lade(kid)
    konzepte = lm.lade()
    ziel_b = _cfg("meilenstein")["ziel_beherrschung"]
    b = [konzepte[k]["beherrschung"] for k in kap["konzepte"]]
    raus = {
        "kapitel": kid, "titel": kap["titel"], "ziel": kap["ziel"],
        "vorwissen": kap["vorwissen"]["status"],
        "konzepte": {"gesamt": len(b), "sitzen": sum(x >= ziel_b for x in b),
                     "im_aufbau": sum(1 <= x < ziel_b for x in b), "neu": sum(x == 0 for x in b)},
        "plan": None,
    }
    plan = kap["plan"]
    if not plan:
        raus["naechster_schritt"] = "/ariadne:vorwissen" if kap["vorwissen"]["status"] != "erledigt" else "/ariadne:plan"
        return raus
    t = heute()
    ist, soll = _ist_anteil(kap, konzepte), _soll_anteil(plan, t)
    # Rückstand in Tagen: an welchem Plantag hätte man den heutigen Ist-Stand erreicht?
    start, ende = date.fromisoformat(plan["start"]), date.fromisoformat(plan["ende"])
    plantag = ende
    for d in range((ende - start).days + 1):
        if _soll_anteil(plan, start + timedelta(days=d)) >= ist - 1e-9:
            plantag = start + timedelta(days=d)
            break
    rueckstand = (t - plantag).days if ist < soll else -max((plantag - t).days, 0)

    ms = []
    for m in plan["meilensteine"]:
        zustand = m["status"]
        if zustand != "bestanden":
            zd = date.fromisoformat(m["zieldatum"])
            zustand = "verpasst" if zd < t else "faellig" if (zd - t).days <= 2 else "offen"
        sitzen = sum(konzepte[k]["beherrschung"] >= ziel_b for k in m["konzepte"])
        ms.append({"id": m["id"], "titel": m["titel"], "zieldatum": m["zieldatum"], "zustand": zustand,
                   "scharf": m.get("scharf", True),
                   "konzepte_sitzen": f"{sitzen}/{len(m['konzepte'])}", "pruefung": m["pruefung"]["art"],
                   "letzter_versuch": m["versuche"][-1]["quote"] if m["versuche"] else None})

    vereinbart_min = plan["budget"]["stunden_pro_woche"] * 60
    zwei_wochen = aktive_minuten(t - timedelta(days=13), t)
    seit_start = max((t - start).days + 1, 1)
    erwartet_14 = vereinbart_min * min(seit_start, 14) / 7
    montag = t - timedelta(days=t.weekday())
    cfg = _cfg("plan")
    gruende = []
    if plan["status"] == "vereinbart":
        if rueckstand >= cfg["neuverhandeln_ab_tagen"]:
            gruende.append(f"{rueckstand} Tage hinter dem Plan")
        if any(m["zustand"] == "verpasst" for m in ms):
            gruende.append("Meilenstein verpasst")
        if seit_start >= 14 and zwei_wochen < 0.6 * erwartet_14:
            gruende.append(f"Lernzeit der letzten zwei Wochen bei {zwei_wochen / erwartet_14:.0%} der vereinbarten")
    raus["plan"] = {
        "version": plan["version"], "status": plan["status"], "start": plan["start"], "ende": plan["ende"],
        "budget": plan["budget"], "machbarkeit": plan["machbarkeit"],
        "ist_anteil": round(ist, 3), "soll_anteil": round(soll, 3), "rueckstand_tage": rueckstand,
        "lernzeit_woche_min": round(aktive_minuten(montag, t)), "vereinbart_woche_min": round(vereinbart_min),
        "lernzeit_14_tage_min": round(zwei_wochen),
        "meilensteine": ms, "neuverhandeln": gruende,
    }
    offen = [m for m in ms if m["zustand"] != "bestanden"]
    if plan["status"] != "vereinbart":
        raus["naechster_schritt"] = "/ariadne:plan (Entwurf verhandeln)"
    elif gruende:
        raus["naechster_schritt"] = "/ariadne:plan (Neuverhandlung)"
    elif offen and not offen[0]["scharf"]:
        raus["naechster_schritt"] = f"/ariadne:plan {kid} ({offen[0]['id']} schärfen)"
    elif offen and offen[0]["zustand"] in ("faellig", "verpasst"):
        raus["naechster_schritt"] = f"/ariadne:meilenstein {kid} {offen[0]['id']}"
    elif offen:
        nicht_sitzend = [k for m in plan["meilensteine"] if m["id"] == offen[0]["id"]
                         for k in m["konzepte"] if konzepte[k]["beherrschung"] < ziel_b]
        raus["naechster_schritt"] = f"/ariadne:lernen {nicht_sitzend[0]}" if nicht_sitzend else f"/ariadne:meilenstein {kid} {offen[0]['id']}"
    else:
        raus["naechster_schritt"] = "Kapitel abgeschlossen – nur noch /ariadne:wiederholen"
    return raus
