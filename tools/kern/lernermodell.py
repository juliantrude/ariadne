"""Das Lernermodell (Abschnitt 5.2). Einziger Schreibweg nach learner/.

Beherrschung ändert sich nur über feste Regeln aus beobachtbaren Fakten:
erreichte Hinweisstufe, Ergebnis des Abrufs, Ergebnis der Vorwissensdiagnose.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone

from fsrs import Card, Rating, Scheduler

from kern.basis import commit, heute, jetzt, lies_json, protokoll, protokolliere, schreib_json, sitzungs_id, wurzel

MAX_BEHERRSCHUNG = 4
# Vorwissen aus einer einzelnen Diagnosefrage hebt nie über 2: eine richtige
# Antwort ist noch kein gesichertes Wissen (Kompetenzillusion, Abschnitt 3.9).
VORWISSEN_BEHERRSCHUNG = {"richtig": 2, "teilweise": 1, "falsch": 0, "uebersprungen": 0}


class Fehler(Exception):
    pass


def konzepte_pfad():
    return wurzel() / "learner" / "konzepte.json"


def kalibrierung_pfad():
    return wurzel() / "learner" / "kalibrierung.csv"


def lade() -> dict[str, dict]:
    return lies_json(konzepte_pfad(), {})


def speichere(konzepte: dict, nachricht: str) -> None:
    schreib_json(konzepte_pfad(), konzepte)
    commit([konzepte_pfad(), kalibrierung_pfad()], f"lm: {nachricht}")


def hole(konzepte: dict, kid: str) -> dict:
    if kid not in konzepte:
        raise Fehler(f"Unbekanntes Konzept: {kid}. Erst mit 'ariadne lm anlegen' anlegen.")
    return konzepte[kid]


def anlegen(kid: str, titel: str, quelle: str = "", voraussetzungen: list[str] | None = None) -> dict:
    konzepte = lade()
    if kid in konzepte:
        raise Fehler(f"Konzept {kid} existiert bereits.")
    for v in voraussetzungen or []:
        if v not in konzepte:
            raise Fehler(f"Voraussetzung {v} existiert nicht. Reihenfolge beachten.")
    konzepte[kid] = {
        "id": kid, "titel": titel, "quelle": quelle, "voraussetzungen": voraussetzungen or [],
        "beherrschung": 0, "fehlvorstellungen": [], "letzte_stufe": None,
        "fsrs": None, "notausgang": 0, "historie": [],
    }
    speichere(konzepte, f"{kid} angelegt")
    protokolliere("anlegen", konzept=kid)
    return konzepte[kid]


# ---------------------------------------------------------------- Hinweisleiter

def stufe(kid: str, stufe: int, schluesselstelle: str = "", notausgang: bool = False) -> dict:
    """Meldet die höchste erreichte Hinweisstufe einer Schlüsselstelle."""
    if not 0 <= stufe <= 4:
        raise Fehler("Stufe muss 0 bis 4 sein (0 = ohne Hilfe gelöst).")
    if notausgang:
        stufe = 4
    konzepte = lade()
    k = hole(konzepte, kid)
    k["letzte_stufe"] = stufe
    if notausgang:
        k["notausgang"] += 1
    if stufe == 4:
        # Wiederholungspflicht: sofort ein Termin, die eigentliche Bewertung kommt mit dem Abruf.
        k["pflicht_termin"] = (heute() + timedelta(days=1)).isoformat()
    speichere(konzepte, f"{kid} Stufe {stufe}{' (Notausgang)' if notausgang else ''}")
    protokolliere("stufe", konzept=kid, stufe=stufe, schluesselstelle=schluesselstelle, notausgang=notausgang)
    return k


def hoechste_stufe_heute(kid: str) -> int:
    sid = sitzungs_id()
    stufen = [e["stufe"] for e in protokoll(tage=1)
              if e["art"] == "stufe" and e["konzept"] == kid and e["sitzung"] == sid]
    return max(stufen, default=0)


# ---------------------------------------------------------------- Bewertung

def bewertung(richtig: bool, stufe: int, erklaerung_traegt: bool, sicherheit: int, schnell: bool) -> tuple[Rating, int]:
    """Tabelle aus Abschnitt 5.2: Beobachtung -> (FSRS-Bewertung, Änderung der Beherrschung)."""
    if not richtig or stufe >= 3:
        return Rating.Again, -1
    if stufe >= 1:
        return Rating.Hard, 0
    if not erklaerung_traegt:
        return Rating.Hard, 0
    if sicherheit == 5 and schnell:
        return Rating.Easy, +1
    return Rating.Good, +1


def _review(k: dict, rating: Rating, zeitpunkt: datetime) -> None:
    karte = Card.from_dict(k["fsrs"]) if k.get("fsrs") else Card()
    karte, _ = Scheduler().review_card(karte, rating, review_datetime=zeitpunkt.astimezone(timezone.utc))
    k["fsrs"] = karte.to_dict()
    k.pop("pflicht_termin", None)


def _kalibrierung(kid: str, sicherheit: int, richtig: bool, quelle: str) -> None:
    pfad = kalibrierung_pfad()
    neu = not pfad.exists()
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "a", newline="") as f:
        w = csv.writer(f)
        if neu:
            w.writerow(["zeit", "konzept", "sicherheit", "richtig", "quelle"])
        w.writerow([jetzt().isoformat(timespec="seconds"), kid, sicherheit, int(richtig), quelle])


def abruf(kid: str, richtig: bool, sicherheit: int, stufe: int | None = None,
          erklaerung_traegt: bool = True, schnell: bool = False, quelle: str = "abruf") -> dict:
    """Ergebnis eines Abrufs. Stufe None = höchste Hinweisstufe dieser Sitzung für das Konzept."""
    if not 1 <= sicherheit <= 5:
        raise Fehler("Sicherheit muss 1 bis 5 sein und vor der Antwort abgefragt werden.")
    if stufe is None:
        stufe = hoechste_stufe_heute(kid)
    konzepte = lade()
    k = hole(konzepte, kid)
    rating, delta = bewertung(richtig, stufe, erklaerung_traegt, sicherheit, schnell)
    vorher = k["beherrschung"]
    k["beherrschung"] = max(0, min(MAX_BEHERRSCHUNG, vorher + delta))
    _review(k, rating, jetzt())
    k["historie"].append({"zeit": jetzt().isoformat(timespec="seconds"), "quelle": quelle, "richtig": richtig,
                          "stufe": stufe, "sicherheit": sicherheit, "bewertung": rating.name,
                          "beherrschung": k["beherrschung"]})
    _kalibrierung(kid, sicherheit, richtig, quelle)
    speichere(konzepte, f"{kid} {rating.name}, Beherrschung {vorher}->{k['beherrschung']} ({quelle})")
    protokolliere("abruf", konzept=kid, richtig=richtig, stufe=stufe, sicherheit=sicherheit,
                  bewertung=rating.name, beherrschung=k["beherrschung"], quelle=quelle)
    return k


# ---------------------------------------------------------------- Vorwissen

def vorwissen(kid: str, ergebnis: str, sicherheit: int | None, selbst: int | None,
              fehlvorstellung: str = "", kapitel: str = "") -> dict:
    """Startwert aus der Vorwissensdiagnose. Überschreibt nie ein Konzept mit eigener Lerngeschichte."""
    if ergebnis not in VORWISSEN_BEHERRSCHUNG:
        raise Fehler(f"Ergebnis muss eins von {sorted(VORWISSEN_BEHERRSCHUNG)} sein.")
    if ergebnis != "uebersprungen" and not (sicherheit and 1 <= sicherheit <= 5):
        raise Fehler("Bei einer Diagnosefrage vorher die Sicherheit 1 bis 5 abfragen.")
    konzepte = lade()
    k = hole(konzepte, kid)
    if k["historie"]:
        protokolliere("vorwissen", konzept=kid, ergebnis=ergebnis, uebernommen=False, kapitel=kapitel)
        return k
    k["beherrschung"] = VORWISSEN_BEHERRSCHUNG[ergebnis]
    k["vorwissen"] = {"zeit": jetzt().isoformat(timespec="seconds"), "ergebnis": ergebnis,
                      "sicherheit": sicherheit, "selbsteinschaetzung": selbst, "kapitel": kapitel}
    if fehlvorstellung:
        k["fehlvorstellungen"].append({"text": fehlvorstellung, "gesehen": heute().isoformat(), "behoben": False})
    if ergebnis == "richtig":
        # Schon gekonnt: in den Wiederholungsplan aufnehmen, damit es geprüft bleibt.
        _review(k, Rating.Good, jetzt())
    if ergebnis != "uebersprungen":
        _kalibrierung(kid, sicherheit, ergebnis == "richtig", f"vorwissen:{kapitel}")
    speichere(konzepte, f"{kid} Vorwissen {ergebnis} -> Beherrschung {k['beherrschung']}")
    protokolliere("vorwissen", konzept=kid, ergebnis=ergebnis, sicherheit=sicherheit, selbst=selbst,
                  uebernommen=True, kapitel=kapitel, beherrschung=k["beherrschung"])
    return k


def fehlvorstellung(kid: str, text: str, behoben: bool = False) -> dict:
    konzepte = lade()
    k = hole(konzepte, kid)
    for f in k["fehlvorstellungen"]:
        if f["text"] == text:
            f["behoben"] = behoben
            break
    else:
        k["fehlvorstellungen"].append({"text": text, "gesehen": heute().isoformat(), "behoben": behoben})
    speichere(konzepte, f"{kid} Fehlvorstellung {'behoben' if behoben else 'gesehen'}: {text[:40]}")
    protokolliere("fehlvorstellung", konzept=kid, text=text, behoben=behoben)
    return k


# ---------------------------------------------------------------- Abfragen

def faellig(bis: datetime | None = None) -> list[dict]:
    bis = bis or jetzt()
    raus = []
    for k in lade().values():
        if k.get("pflicht_termin") and k["pflicht_termin"] <= bis.date().isoformat():
            raus.append(k)
        elif k.get("fsrs") and datetime.fromisoformat(k["fsrs"]["due"]) <= bis:
            raus.append(k)
    return raus
