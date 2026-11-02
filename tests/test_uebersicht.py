"""Der Stand für das Dashboard: Statistik, Termine, nächste Schritte, nichts Vorweggenommenes."""
import json

from test_planung import KONZEPTE, kapitel, vorwissen_erledigt  # noqa: F401

from kern import lernermodell as lm
from kern import planung as pl
from kern.uebersicht import uebersicht


def test_leeres_lernrepo(repo):
    u = uebersicht()
    assert u["kapitel"] == [] and u["deadlines"] == [] and u["wiederholung"]["faellig"] == 0
    assert u["statistik"]["abrufe"] == {"gesamt": 0, "richtig": 0} and u["statistik"]["hinweise"]["schnitt"] is None
    assert u["koennen"]["fazit"] == "Noch keine Konzepte." and u["koennen"]["bereiche"] == []
    assert [a["befehl"] for a in u["aktionen"]] == ["/ariadne:fortschritt", "/ariadne:bilanz", "/ariadne:kapitel"]


def test_statistik_zaehlt_abrufe(kapitel):  # noqa: F811
    lm.abruf("os.sync.mutex", richtig=True, sicherheit=4, stufe=0)
    lm.abruf("os.vm.tlb", richtig=False, sicherheit=2, stufe=0)
    assert uebersicht()["statistik"]["abrufe"] == {"gesamt": 2, "richtig": 1}


def _sitzt(kid: str) -> None:
    konzepte = lm.lade()
    konzepte[kid]["beherrschung"] = 3
    konzepte[kid]["historie"] = [{"zeit": "2026-11-01T10:00:00+01:00", "richtig": True, "sicherheit": 4}]
    lm.speichere(konzepte, "Test")


def test_matrix_zaehlt_stufen_je_bereich_und_kapitel(kapitel):  # noqa: F811
    _sitzt("os.sync.mutex")
    lm.vorwissen("os.vm.adresse", "richtig", sicherheit=5, selbst=5, kapitel="os")
    lm.fehlvorstellung("os.vm.tlb", "TLB speichert Daten")
    lm.stufe("os.vm.tlb", 2)
    k = uebersicht()["koennen"]
    assert [(z["name"], z["stufen"]) for z in k["bereiche"]] == [("os.vm", [3, 0, 1, 0, 0]), ("os.sync", [1, 0, 0, 1, 0])]
    vm = k["bereiche"][0]
    assert (vm["fehlvorstellungen"], vm["hilfe"], vm["sitzen"]) == (1, 2.0, 0)
    assert k["kapitel"][0]["name"] == "Betriebssysteme" and k["kapitel"][0]["stufen"] == [4, 0, 1, 1, 0]


def test_vorwissen_allein_sitzt_nie(kapitel):  # noqa: F811
    lm.vorwissen("os.vm.adresse", "richtig", sicherheit=5, selbst=5, kapitel="os")
    assert uebersicht()["koennen"]["sitzen"] == 0


def test_offene_fehlvorstellung_laesst_ein_sitzendes_konzept_wackeln(kapitel):  # noqa: F811
    _sitzt("os.sync.mutex")
    assert uebersicht()["koennen"]["wackeln"] == 0
    lm.fehlvorstellung("os.sync.mutex", "Mutex ist ein Semaphor")
    k = uebersicht()["koennen"]
    assert (k["sitzen"], k["wackeln"]) == (1, 1) and k["schwaechen"][0]["grund"] == "1 Fehlvorstellung offen"
    assert k["fazit"] == "1 von 6 Konzepten sitzen, 1 davon wackeln. Am schwächsten: os.vm."


def test_schwaechen_stehen_nach_dringlichkeit_und_bereiche_schwaechste_zuerst(kapitel):  # noqa: F811
    _sitzt("os.sync.mutex")
    lm.abruf("os.vm.adresse", richtig=False, sicherheit=2, stufe=0)
    lm.abruf("os.vm.tlb", richtig=False, sicherheit=5, stufe=0)
    k = uebersicht()["koennen"]
    assert [(w["id"], w["grund"]) for w in k["schwaechen"]] == [
        ("os.vm.tlb", "warst dir sicher, lagst aber falsch"), ("os.vm.adresse", "zuletzt falsch")]
    assert k["schwaechen"][0]["befehl"] == "/ariadne:lernen os.vm.tlb"
    assert [z["name"] for z in k["bereiche"]] == ["os.vm", "os.sync"]


def test_kalibrierung_und_hinweise(kapitel):  # noqa: F811
    lm.abruf("os.vm.tlb", richtig=False, sicherheit=5, stufe=0)
    lm.abruf("os.vm.adresse", richtig=True, sicherheit=1, stufe=0)
    lm.stufe("os.sync.mutex", 2)
    lm.stufe("os.sync.mutex", 1, notausgang=True)
    s = uebersicht()["statistik"]
    assert s["kalibrierung"] == {"hoch": {"gesamt": 1, "richtig": 0}, "niedrig": {"gesamt": 1, "richtig": 1}}
    assert s["hinweise"] == {"anzahl": 2, "schnitt": 3.0, "stufe_4": 1, "notausgang": 1}


def test_mehr_fehlvorstellungen_gehen_vor(kapitel):  # noqa: F811
    lm.fehlvorstellung("os.sync.mutex", "eins")
    for text in ("eins", "zwei"):
        lm.fehlvorstellung("os.vm.tlb", text)
    lm.abruf("os.sync.mutex", richtig=True, sicherheit=3, stufe=0)
    lm.abruf("os.vm.tlb", richtig=True, sicherheit=3, stufe=0)
    assert [w["id"] for w in uebersicht()["koennen"]["schwaechen"]] == ["os.vm.tlb", "os.sync.mutex"]


def test_klausur_zeigt_wie_viel_sitzt(kapitel):  # noqa: F811
    _sitzt("os.sync.mutex")
    assert uebersicht()["koennen"]["klausuren"] == [
        {"titel": "Betriebssysteme", "art": "klausur", "datum": "2026-12-14", "tage": 42, "gesamt": 6,
         "sitzen": 1, "wackeln": 0}]


def test_alles_sicher_wird_klar_gesagt(repo):
    lm.anlegen("a.b.c", "C")
    _sitzt("a.b.c")
    assert uebersicht()["koennen"]["fazit"] == "Alle 1 Konzepte sitzen, belegt durch deine Abrufe."


def test_termine_kennen_ziel_und_nur_vereinbarte_meilensteine(kapitel):  # noqa: F811
    vorwissen_erledigt()
    pl.vorschlag("os", stunden_pro_woche=4, sitzungen_pro_woche=2, energie="mittel")
    assert [d["art"] for d in uebersicht()["deadlines"]] == ["ziel"]
    pl.vereinbaren("os", "passt so")
    termine = uebersicht()["deadlines"]
    assert {"ziel", "meilenstein"} == {d["art"] for d in termine}
    assert [d["datum"] for d in termine] == sorted(d["datum"] for d in termine)
    assert termine[-1]["tage"] > 0 and termine[0]["zustand"] in ("offen", "faellig")


def test_aktionen_sind_reine_befehle_und_stehen_nach_dringlichkeit(kapitel, monkeypatch):  # noqa: F811
    vorwissen_erledigt()
    pl.vorschlag("os", stunden_pro_woche=4, sitzungen_pro_woche=2, energie="mittel")
    lm.stufe("os.vm.tlb", 4)
    monkeypatch.setenv("ARIADNE_JETZT", "2026-11-03T10:00:00+01:00")
    aktionen = uebersicht()["aktionen"]
    assert aktionen[0]["befehl"] == "/ariadne:wiederholen"
    assert aktionen[1] == {"titel": "Betriebssysteme", "befehl": "/ariadne:plan"}


def test_uebersicht_verrät_keine_kartenfragen(kapitel):  # noqa: F811
    (kapitel / ".tutor" / "karten" / "os.vm.tlb.md").write_text("GEHEIME ANTWORT")
    assert "GEHEIME" not in json.dumps(uebersicht(), ensure_ascii=False)


def test_kaputtes_kapitel_verdeckt_den_rest_nicht(kapitel):  # noqa: F811
    (kapitel / "learner" / "kapitel" / "b.json").write_text(json.dumps({"id": "b", "titel": "Kaputt"}))
    u = uebersicht()
    assert [k.get("fehler") is not None for k in u["kapitel"]] == [True, False]


def test_dashboard_markdown_zeigt_stufen_als_heatmap(kapitel):  # noqa: F811
    from kern.dashboard import markdown

    vorwissen_erledigt()
    pl.vorschlag("os", stunden_pro_woche=4, sitzungen_pro_woche=2, energie="mittel")
    pl.vereinbaren("os", "passt so")
    lm.abruf("os.vm.tlb", richtig=False, sicherheit=5, stufe=0)
    md = markdown(uebersicht())
    for karte in ("## Überblick", "## Beherrschung je Kapitel", "## Beherrschung je Bereich", "## Zuerst angehen",
                  "## Plan: Betriebssysteme", "## Termine", "## Lernzeit, 14 Tage", "## Selbsteinschätzung, 14 Tage"):
        assert karte in md
    fence = md.split("## Beherrschung je Bereich")[1].split("```chart\n")[1].split("\n```")[0]
    chart = json.loads(fence)
    assert chart["type"] == "heatmap" and [s["label"] for s in chart["series"]] == ["0", "1", "2", "3", "4"]
    assert "- [ ] M1" in md


def test_dashboard_markdown_kommt_mit_leerem_repo_klar(repo):
    from kern.dashboard import markdown

    md = markdown(uebersicht())
    assert "Noch keine Konzepte." in md and "Keine Termine." in md and "Beherrschung je" not in md
