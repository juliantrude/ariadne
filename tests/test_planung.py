"""Kapitel, Vorwissen, Lehrplan mit Verhandlung, Meilensteine, Fortschritt."""
import json

import pytest
from conftest import blockiert, hook, transkript

from kern import lernermodell as lm
from kern import planung as pl

KONZEPTE = [("os.vm.adresse", "Adressübersetzung", []), ("os.vm.seitentabelle", "Seitentabelle", ["os.vm.adresse"]),
            ("os.vm.tlb", "TLB", ["os.vm.seitentabelle"]), ("os.vm.pagefault", "Page Fault", ["os.vm.seitentabelle"]),
            ("os.sync.mutex", "Mutex", []), ("os.sync.semaphor", "Semaphor", ["os.sync.mutex"])]


@pytest.fixture
def kapitel(repo):
    for kid, titel, vor in KONZEPTE:
        lm.anlegen(kid, titel, voraussetzungen=vor)
    pl.neu("os", "Betriebssysteme", ["os."], "klausur", "2026-12-14", stichworte=["Betriebssysteme"])
    return repo


def vorwissen_erledigt():
    lm.vorwissen("os.vm.adresse", "richtig", sicherheit=4, selbst=3, kapitel="os")
    lm.vorwissen("os.vm.seitentabelle", "teilweise", sicherheit=3, selbst=3, kapitel="os")
    pl.vorwissen_abschliessen("os", "Grundlagen da, Synchronisation neu.", ["Documents/uni/user-profil"])


def test_neu_mit_praefix_und_unbekanntem_konzept(kapitel):
    assert len(pl.lade("os")["konzepte"]) == 6
    with pytest.raises(pl.Fehler):
        pl.neu("x", "X", ["gibt.es.nicht"], "klausur", None)


def test_plan_erst_nach_vorwissensanalyse(kapitel):
    with pytest.raises(pl.Fehler, match="Vorwissensanalyse"):
        pl.vorschlag("os", 5, 3, "mittel")


def test_vorwissen_haelt_startstand_und_luecken_fest(kapitel):
    vorwissen_erledigt()
    vw = pl.lade("os")["vorwissen"]
    assert vw["start_beherrschung"]["os.vm.adresse"] == 2 and vw["start_beherrschung"]["os.vm.seitentabelle"] == 1
    assert "os.sync.mutex" in vw["ohne_diagnose"] and vw["gedaechtnis_genutzt"] == ["Documents/uni/user-profil"]


def test_vorschlag_rechnet_aufwand_und_termine(kapitel):
    vorwissen_erledigt()
    plan = pl.vorschlag("os", stunden_pro_woche=4, sitzungen_pro_woche=2, energie="mittel")["plan"]
    # Aufwand: B2 35, B1 60, viermal B0 90 = 455 min, +20 % Wiederholung, +2×30 Prüfung, +15 % Puffer
    assert plan["minuten_gesamt"] == round((455 * 1.2 + 60) * 1.15)
    assert [m["id"] for m in plan["meilensteine"]] == ["M1", "M2"]
    reihenfolge = [k for m in plan["meilensteine"] for k in m["konzepte"]]
    for kid, _, vor in KONZEPTE:  # Voraussetzungen kommen immer vorher
        assert all(reihenfolge.index(v) < reihenfolge.index(kid) for v in vor)
    assert plan["status"] == "entwurf" and plan["machbarkeit"]["machbar"]


def test_energie_begrenzt_neue_konzepte(kapitel):
    vorwissen_erledigt()
    viel_zeit = pl.vorschlag("os", 20, 1, "niedrig")["plan"]
    # 5 Konzepte unter B2 bei 1 Sitzung × 1 neues Konzept pro Woche: mindestens 5 Wochen, obwohl Zeit reichlich da ist
    assert viel_zeit["ende"] >= "2026-12-07"


def test_nicht_machbar_liefert_verhandlungsgrundlage(kapitel):
    vorwissen_erledigt()
    m = pl.vorschlag("os", 0.5, 1, "mittel")["plan"]["machbarkeit"]
    assert not m["machbar"] and m["fehlende_tage"] > 0
    assert m["noetige_stunden_pro_woche"] > 0.5 and isinstance(m["passt_bis_ziel"], list)


def test_gliederung_vom_modell_wird_geprueft(kapitel):
    vorwissen_erledigt()
    falsch_rum = [{"titel": "Sync", "konzepte": ["os.vm.tlb", "os.sync.mutex", "os.sync.semaphor", "os.vm.pagefault"]},
                  {"titel": "VM", "konzepte": ["os.vm.adresse", "os.vm.seitentabelle"]}]
    with pytest.raises(pl.Fehler, match="braucht"):
        pl.vorschlag("os", 5, 3, "mittel", falsch_rum)
    unvollstaendig = [{"titel": "VM", "konzepte": ["os.vm.adresse"]}]
    with pytest.raises(pl.Fehler, match="fehlen"):
        pl.vorschlag("os", 5, 3, "mittel", unvollstaendig)
    challenge_ohne_kriterien = [{"titel": "Alles", "konzepte": [k for k, _, _ in KONZEPTE],
                                 "pruefung": {"art": "challenge", "beschreibung": "perf-Experiment"}}]
    with pytest.raises(pl.Fehler, match="kriterien"):
        pl.vorschlag("os", 5, 3, "mittel", challenge_ohne_kriterien)


def test_vereinbaren_prueft_zustimmung_im_transkript(kapitel, tmp_path, monkeypatch):
    vorwissen_erledigt()
    pl.vorschlag("os", 5, 3, "mittel")
    t = transkript(tmp_path / "t.jsonl", [("user", "Passt, so machen wir das!"), ("assistant", "Gut.")])
    monkeypatch.setenv("ARIADNE_TRANSCRIPT", str(t))
    with pytest.raises(pl.Fehler, match="steht so nicht"):
        pl.vereinbaren("os", "Ja, einverstanden")
    plan = pl.vereinbaren("os", "passt, so machen wir das")["plan"]
    assert plan["status"] == "vereinbart" and plan["zustimmung"] == "passt, so machen wir das"


def test_stop_hook_faengt_erfundene_zustimmung(kapitel, tmp_path):
    vorwissen_erledigt()
    pl.vorschlag("os", 5, 3, "mittel")
    pl.vereinbaren("os", "Klingt gut")  # ohne ARIADNE_TRANSCRIPT, also erst der Stop-Hook
    t = transkript(tmp_path / "t.jsonl", [("user", "Hmm, ich weiß nicht."), ("assistant", "Dann so.")])
    aus = hook("stop_check.py", {"session_id": "s1", "transcript_path": str(t)})
    assert "zuruecknehmen" in blockiert(aus)
    pl.zuruecknehmen("os")
    assert hook("stop_check.py", {"session_id": "s1", "transcript_path": str(t)}) is None


def vereinbart(gliederung=None):
    vorwissen_erledigt()
    pl.vorschlag("os", 5, 3, "mittel", gliederung)
    pl.vereinbaren("os", "ok")


def test_meilensteinpruefung_misst_und_bewertet(kapitel):
    vereinbart()
    m1 = pl.lade("os")["plan"]["meilensteine"][0]
    with pytest.raises(pl.Fehler, match="läuft keine"):
        pl.pruefung_item("os", "M1", "richtig", 4, konzept=m1["konzepte"][0])
    pl.pruefung_start("os", "M1")
    for k in m1["konzepte"][:-1]:
        pl.pruefung_item("os", "M1", "richtig", 4, konzept=k)
    with pytest.raises(pl.Fehler, match="Noch nicht geprüft"):
        pl.pruefung_auswerten("os", "M1")
    pl.pruefung_item("os", "M1", "teilweise", 2, konzept=m1["konzepte"][-1])
    v = pl.pruefung_auswerten("os", "M1")
    assert v["quote"] == round(3.5 / 4, 3) and v["bestanden"] and v["schwache"] == [m1["konzepte"][-1]]
    # Prüfungsitems zählen als Abruf ohne Hilfe im Lernermodell
    assert lm.lade()[m1["konzepte"][0]]["historie"][-1]["quelle"] == "meilenstein:os:M1"


def test_challenge_mit_kriterien(kapitel):
    alle = [k for k, _, _ in KONZEPTE]
    vereinbart([{"titel": "Alles", "konzepte": alle, "pruefung": {
        "art": "challenge", "beschreibung": "TLB-Effekt mit perf messen und erklären",
        "kriterien": ["Vorhersage begründet", "Messung korrekt", "Erklärung trägt"], "schwelle": 0.7}}])
    pl.pruefung_start("os", "M1")
    pl.pruefung_item("os", "M1", "richtig", 4, kriterium="Vorhersage begründet")
    pl.pruefung_item("os", "M1", "falsch", 3, kriterium="Messung korrekt")
    pl.pruefung_item("os", "M1", "richtig", 4, kriterium="Erklärung trägt")
    v = pl.pruefung_auswerten("os", "M1")
    assert not v["bestanden"] and v["quote"] == round(2 / 3, 3)


def test_status_zeigt_rueckstand_und_empfiehlt_neuverhandlung(kapitel, monkeypatch):
    vereinbart()
    s = pl.status("os")["plan"]
    assert s["rueckstand_tage"] == 0 and s["ist_anteil"] == 0
    monkeypatch.setenv("ARIADNE_JETZT", "2026-11-23T10:00:00+01:00")  # drei Wochen später, nichts gelernt
    s = pl.status("os")
    assert s["plan"]["rueckstand_tage"] >= 7 and s["plan"]["soll_anteil"] > 0.3
    assert any("hinter dem Plan" in g for g in s["plan"]["neuverhandeln"])
    assert any("Lernzeit" in g for g in s["plan"]["neuverhandeln"])
    assert s["naechster_schritt"] == "/ariadne:plan (Neuverhandlung)"


def test_fortschritt_durch_lernen(kapitel, monkeypatch):
    vereinbart()
    for _ in range(3):
        for k in ("os.vm.adresse", "os.vm.seitentabelle", "os.vm.tlb"):
            lm.abruf(k, richtig=True, sicherheit=4, stufe=0)
    s = pl.status("os")["plan"]
    assert s["ist_anteil"] > s["soll_anteil"] and s["rueckstand_tage"] < 0  # voraus


def test_neuverhandlung_behaelt_bestandene_meilensteine(kapitel, monkeypatch):
    vereinbart()
    m1 = pl.lade("os")["plan"]["meilensteine"][0]
    pl.pruefung_start("os", "M1")
    for k in m1["konzepte"]:
        pl.pruefung_item("os", "M1", "richtig", 4, konzept=k)
    pl.pruefung_auswerten("os", "M1")
    monkeypatch.setenv("ARIADNE_JETZT", "2026-11-20T10:00:00+01:00")
    kap = pl.vorschlag("os", 8, 4, "hoch", notiz="Mehr Zeit nach Abgabe des Projekts")
    plan = kap["plan"]
    assert plan["version"] == 2 and plan["status"] == "entwurf" and plan["start"] == "2026-11-20"
    assert plan["meilensteine"][0]["id"] == "M1" and plan["meilensteine"][0]["status"] == "bestanden"
    assert plan["meilensteine"][1]["id"] == "M2" and plan["ist_basis"] > 0
    assert kap["plan_historie"][0]["version"] == 1
    assert pl.status("os")["plan"]["soll_anteil"] == plan["ist_basis"]


def test_lernzeit_wird_gemessen(kapitel):
    vereinbart()
    for minute in (0, 5, 12, 60, 61):
        with open(kapitel / "sitzungen" / "2026-11-02" / "aktivitaet.jsonl", "a") as f:
            f.write(json.dumps({"zeit": f"2026-11-02T10:{minute % 60:02d}:00+01:00" if minute < 60
                                else f"2026-11-02T11:{minute - 60:02d}:00+01:00", "sitzung": "s1"}) + "\n")
    # 0→5→12: 12 min, Pause 48 min zählt 2 min, 60→61: 1 min, plus 2 min Start = 17 min
    assert pl.status("os")["plan"]["lernzeit_woche_min"] == 17
