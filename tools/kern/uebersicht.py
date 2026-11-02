"""Alles, was das Dashboard zeigt, an einer Stelle gerechnet: Stand der Kapitel, Stärken und Schwächen, Termine, nächste Schritte.
Nur lesend. Enthält keine Karteninhalte und keine Prüfungsfragen, das Dashboard darf nichts vorwegnehmen."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from kern import lernermodell as lm
from kern import planung as pl
from kern.basis import heute, jetzt, protokoll
from kern.zeit import aktive_minuten

STATISTIK_TAGE = 14
VORSCHAU_TAGE = 7
SICHER_GEFUEHLT = 4  # ab dieser Selbsteinschätzung ist eine falsche Antwort eine Kompetenzillusion (Abschnitt 3.9)
UNSICHER_GEFUEHLT = 2
MAX_SCHWAECHEN = 5
FESTE_AKTIONEN = (("Lernstand erklären", "/ariadne:fortschritt"), ("Bilanz ziehen", "/ariadne:bilanz"),
                  ("Neues Kapitel", "/ariadne:kapitel"))


def _kapitel() -> list[dict]:
    raus = []
    for kap in pl.alle():
        try:
            raus.append(pl.status(kap["id"]))
        except Exception as e:  # ein kaputtes Kapitel darf den Rest nicht verdecken
            raus.append({"kapitel": kap.get("id"), "titel": kap.get("titel", kap.get("id")), "fehler": str(e)})
    return raus


def _treffer(abrufe: list[dict]) -> dict:
    return {"gesamt": len(abrufe), "richtig": sum(h["richtig"] for h in abrufe)}


def _statistik(konzepte: dict) -> dict:
    t = heute()
    tage = [t - timedelta(days=i) for i in range(STATISTIK_TAGE)]
    grenze = jetzt() - timedelta(days=STATISTIK_TAGE)
    abrufe = [h for k in konzepte.values() for h in k["historie"] if datetime.fromisoformat(h["zeit"]) >= grenze]
    stufen = [e for e in protokoll(tage=STATISTIK_TAGE) if e["art"] == "stufe"]
    return {"abrufe": _treffer(abrufe),
            "kalibrierung": {"hoch": _treffer([h for h in abrufe if h["sicherheit"] >= SICHER_GEFUEHLT]),
                             "niedrig": _treffer([h for h in abrufe if h["sicherheit"] <= UNSICHER_GEFUEHLT])},
            "hinweise": {"anzahl": len(stufen),
                         "schnitt": round(sum(e["stufe"] for e in stufen) / len(stufen), 1) if stufen else None,
                         "stufe_4": sum(e["stufe"] == 4 for e in stufen),
                         "notausgang": sum(bool(e.get("notausgang")) for e in stufen)},
            "lernzeit_tage": [{"datum": d.isoformat(), "minuten": round(aktive_minuten(d, d))} for d in reversed(tage)],
            "lernzeit_min": round(aktive_minuten(tage[-1], t)),
            "lerntage": sum(aktive_minuten(d, d) > 0 for d in tage)}


def _offen(k: dict) -> int:
    return sum(not f["behoben"] for f in k["fehlvorstellungen"])


def _grund(k: dict, faellig: set[str]) -> tuple[int, str]:
    """Warum ein Konzept unsicher ist, das Dringendste zuerst. Der Rang ordnet die Schwächen."""
    letzter = k["historie"][-1] if k["historie"] else None
    offen = _offen(k)
    if letzter and not letzter["richtig"] and letzter["sicherheit"] >= SICHER_GEFUEHLT:
        return 0, "warst dir sicher, lagst aber falsch"
    if offen:
        return 1, f"{offen} Fehlvorstellung{'en' if offen > 1 else ''} offen"
    if letzter and not letzter["richtig"]:
        return 2, "zuletzt falsch"
    if k.get("letzte_stufe"):
        return 3, "nur mit Hinweisen gelöst"
    if k["id"] in faellig:
        return 4, "Wiederholung fällig"
    return 5, "noch nicht oft genug abgerufen"


def _bereich(kid: str) -> str:
    teile = kid.split(".")  # kurs.bereich.konzept
    return ".".join(teile[:2]) if len(teile) > 2 else teile[0]


def _hat_belege(k: dict) -> bool:
    return bool(k["historie"]) or k.get("vorwissen", {}).get("ergebnis", "uebersprungen") != "uebersprungen"


def _wackelt(k: dict, faellig: set[str]) -> bool:
    return k["id"] in faellig or _offen(k) > 0


def _zeile(name: str, ids: list[str], konzepte: dict, faellig: set[str], ziel: int) -> dict:
    """Eine Zeile der Matrix: wie viele Konzepte auf welcher Beherrschungsstufe stehen, und was daran noch wackelt."""
    ks = [konzepte[i] for i in ids]
    hilfe = [k["letzte_stufe"] for k in ks if k["letzte_stufe"] is not None]
    return {"name": name, "gesamt": len(ks),
            "stufen": [sum(k["beherrschung"] == b for k in ks) for b in range(lm.MAX_BEHERRSCHUNG + 1)],
            "schnitt": sum(k["beherrschung"] for k in ks) / len(ks) if ks else 0.0,
            "sitzen": sum(k["beherrschung"] >= ziel for k in ks),
            "wackeln": sum(k["beherrschung"] >= ziel and _wackelt(k, faellig) for k in ks),
            "faellig": sum(k["id"] in faellig for k in ks),
            "fehlvorstellungen": sum(_offen(k) for k in ks),
            "hilfe": round(sum(hilfe) / len(hilfe), 1) if hilfe else None}


def _klausuren(konzepte: dict, faellig: set[str], ziel: int) -> list[dict]:
    t, raus = heute(), []
    for kap in pl.alle():
        termin = (kap.get("ziel") or {}).get("datum")
        if termin and date.fromisoformat(termin) >= t:
            z = _zeile(kap["titel"], [k for k in kap.get("konzepte", []) if k in konzepte], konzepte, faellig, ziel)
            raus.append({"titel": kap["titel"], "art": kap["ziel"]["art"], "datum": termin,
                         "tage": (date.fromisoformat(termin) - t).days,
                         "gesamt": z["gesamt"], "sitzen": z["sitzen"], "wackeln": z["wackeln"]})
    return sorted(raus, key=lambda d: d["datum"])


def _koennen(konzepte: dict) -> dict:
    faellig = {k["id"] for k in lm.faellig()}
    ziel = pl.ziel_beherrschung()

    gruppen: dict[str, list[str]] = {}
    for kid in konzepte:
        gruppen.setdefault(_bereich(kid), []).append(kid)
    bereiche = sorted((_zeile(n, ids, konzepte, faellig, ziel) for n, ids in gruppen.items()),
                      key=lambda z: (z["schnitt"], -z["fehlvorstellungen"], z["name"]))
    kapitel = [_zeile(kap.get("titel", kap["id"]), [k for k in kap.get("konzepte", []) if k in konzepte],
                      konzepte, faellig, ziel) for kap in pl.alle()]

    schwach = [k for k in konzepte.values()
               if _hat_belege(k) and (k["beherrschung"] < ziel or _wackelt(k, faellig))]
    bewertet = sorted(((_grund(k, faellig), k) for k in schwach),
                      key=lambda p: (p[0][0], -_offen(p[1]), p[1]["beherrschung"], p[1]["id"]))
    schwaechen = [{"id": k["id"], "titel": k["titel"], "grund": g[1], "befehl": f"/ariadne:lernen {k['id']}"}
                  for g, k in bewertet[:MAX_SCHWAECHEN]]

    sitzen = sum(k["beherrschung"] >= ziel for k in konzepte.values())
    wackeln = sum(k["beherrschung"] >= ziel and _wackelt(k, faellig) for k in konzepte.values())
    if not konzepte:
        fazit = "Noch keine Konzepte."
    elif sitzen == len(konzepte) and not wackeln:
        fazit = f"Alle {sitzen} Konzepte sitzen, belegt durch deine Abrufe."
    else:
        fazit = f"{sitzen} von {len(konzepte)} Konzepten sitzen"
        fazit += f", {wackeln} davon wackeln" if wackeln else ""
        fazit += f". Am schwächsten: {bereiche[0]['name']}."
    return {"fazit": fazit, "gesamt": len(konzepte), "sitzen": sitzen, "wackeln": wackeln, "ziel": ziel,
            "bereiche": bereiche, "kapitel": kapitel, "schwaechen": schwaechen,
            "weitere_schwaechen": max(len(schwach) - MAX_SCHWAECHEN, 0),
            "klausuren": _klausuren(konzepte, faellig, ziel)}


def _wiederholung() -> dict:
    faellig = lm.faellig()
    return {"faellig": len(faellig), "ids": [k["id"] for k in faellig[:12]],
            "bald": len(lm.faellig(jetzt() + timedelta(days=VORSCHAU_TAGE))) - len(faellig)}


def _deadlines(kapitel: list[dict]) -> list[dict]:
    """Ziele und Meilensteine vereinbarter Pläne. Ein Entwurf ist noch kein Termin."""
    t, raus = heute(), []

    def eintrag(datum: str, art: str, s: dict, titel: str, zustand: str) -> dict:
        return {"datum": datum, "tage": (date.fromisoformat(datum) - t).days, "art": art,
                "kapitel": s["kapitel"], "titel": titel, "zustand": zustand}

    for s in kapitel:
        if "fehler" in s:
            continue
        if s["ziel"]["datum"]:
            zustand = "verpasst" if date.fromisoformat(s["ziel"]["datum"]) < t else "offen"
            raus.append(eintrag(s["ziel"]["datum"], "ziel", s, s["ziel"]["art"], zustand))
        if s["plan"] and s["plan"]["status"] == "vereinbart":
            raus += [eintrag(m["zieldatum"], "meilenstein", s, f"{m['id']} {m['titel']}", m["zustand"])
                     for m in s["plan"]["meilensteine"] if m["zustand"] != "bestanden"]
    return sorted(raus, key=lambda d: (d["datum"], d["kapitel"]))


def _aktionen(kapitel: list[dict], wiederholung: dict) -> list[dict]:
    raus = []
    if wiederholung["faellig"]:
        raus.append({"titel": f"{wiederholung['faellig']} Wiederholungen", "befehl": "/ariadne:wiederholen"})
    for s in kapitel:
        schritt = s.get("naechster_schritt", "")
        if schritt.startswith("/ariadne:"):  # Text in Klammern erklärt den Schritt, gehört aber nicht zum Befehl
            raus.append({"titel": s["titel"], "befehl": schritt.split(" (")[0]})
    raus += [{"titel": titel, "befehl": befehl} for titel, befehl in FESTE_AKTIONEN]
    eindeutig: dict[str, dict] = {}
    for a in raus:
        eindeutig.setdefault(a["befehl"], a)
    return list(eindeutig.values())


def uebersicht() -> dict:
    kapitel = _kapitel()
    wiederholung = _wiederholung()
    return {"heute": heute().isoformat(), "kapitel": kapitel, "wiederholung": wiederholung,
            "koennen": _koennen(lm.lade()), "statistik": _statistik(lm.lade()), "deadlines": _deadlines(kapitel),
            "aktionen": _aktionen(kapitel, wiederholung)}
