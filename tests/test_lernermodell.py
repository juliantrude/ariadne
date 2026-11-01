"""T5, T6, T8 und die Vorwissensregeln."""
import json

import pytest
from conftest import blockiert, hook
from fsrs import Rating

from kern import lernermodell as lm


@pytest.fixture
def tlb(repo):
    lm.anlegen("os.vm.seitentabelle", "Seitentabelle")
    lm.anlegen("os.vm.tlb", "TLB", voraussetzungen=["os.vm.seitentabelle"])
    return repo


@pytest.mark.parametrize("richtig,stufe,erkl,sich,schnell,erwartet", [
    (True, 0, True, 4, False, (Rating.Good, +1)),
    (True, 0, True, 5, True, (Rating.Easy, +1)),
    (True, 0, False, 4, False, (Rating.Hard, 0)),
    (True, 1, True, 4, False, (Rating.Hard, 0)),
    (True, 2, True, 4, False, (Rating.Hard, 0)),
    (True, 3, True, 4, False, (Rating.Again, -1)),
    (True, 4, True, 4, False, (Rating.Again, -1)),
    (False, 0, True, 4, False, (Rating.Again, -1)),
])
def test_t8_bewertungstabelle(richtig, stufe, erkl, sich, schnell, erwartet):
    assert lm.bewertung(richtig, stufe, erkl, sich, schnell) == erwartet


def test_abruf_nutzt_hoechste_stufe_der_sitzung(tlb):
    lm.stufe("os.vm.tlb", 1)
    lm.stufe("os.vm.tlb", 3)
    k = lm.abruf("os.vm.tlb", richtig=True, sicherheit=4)
    assert k["historie"][-1]["bewertung"] == "Again" and k["beherrschung"] == 0
    assert (tlb / "learner" / "kalibrierung.csv").read_text().count("\n") == 2


def test_beherrschung_bleibt_in_grenzen(tlb):
    for _ in range(6):
        k = lm.abruf("os.vm.seitentabelle", richtig=True, sicherheit=4, stufe=0)
    assert k["beherrschung"] == 4


def test_stufe_4_setzt_wiederholungstermin(tlb):
    k = lm.stufe("os.vm.tlb", 4, notausgang=True)
    assert k["pflicht_termin"] == "2026-11-03" and k["notausgang"] == 1
    assert [x["id"] for x in lm.faellig(lm.jetzt().replace(day=3))] == ["os.vm.tlb"]


def test_vorwissen_hebt_hoechstens_auf_2(tlb):
    k = lm.vorwissen("os.vm.seitentabelle", "richtig", sicherheit=5, selbst=4, kapitel="os")
    assert k["beherrschung"] == 2 and k["fsrs"] is not None
    k = lm.vorwissen("os.vm.tlb", "falsch", sicherheit=4, selbst=3, fehlvorstellung="TLB-Miss = Page Fault")
    assert k["beherrschung"] == 0 and k["fehlvorstellungen"][0]["behoben"] is False


def test_vorwissen_ueberschreibt_keine_lerngeschichte(tlb):
    lm.abruf("os.vm.tlb", richtig=True, sicherheit=3, stufe=0)
    k = lm.vorwissen("os.vm.tlb", "falsch", sicherheit=2, selbst=1)
    assert k["beherrschung"] == 1 and "vorwissen" not in k


def test_vorwissen_verlangt_sicherheit(tlb):
    with pytest.raises(lm.Fehler):
        lm.vorwissen("os.vm.tlb", "richtig", sicherheit=None, selbst=3)


def test_t5_edit_auf_learner_wird_abgewiesen(tlb):
    for werkzeug, eingabe in [("Edit", {"file_path": str(tlb / "learner" / "konzepte.json")}),
                              ("Write", {"file_path": "learner/kapitel/os.json"}),
                              ("Bash", {"command": "echo '{}' > learner/konzepte.json"}),
                              ("Bash", {"command": "sed -i s/0/4/ learner/konzepte.json"}),
                              ("Bash", {"command": "python3 -c \"open('learner/x','w')\""})]:
        aus = hook("guard_learner.py", {"tool_name": werkzeug, "tool_input": eingabe})
        assert aus["hookSpecificOutput"]["permissionDecision"] == "deny", (werkzeug, eingabe)


def test_t5_erlaubte_zugriffe(tlb):
    for werkzeug, eingabe in [("Bash", {"command": "uv run python tools/lm.py abruf os.vm.tlb --richtig --sicherheit 3"}),
                              ("Bash", {"command": "cat learner/konzepte.json"}),
                              ("Write", {"file_path": str(tlb / ".tutor" / "karten" / "tlb.yaml")})]:
        assert hook("guard_learner.py", {"tool_name": werkzeug, "tool_input": eingabe}) is None


def test_t6_stufe_4_ohne_termin_blockiert(tlb, tmp_path):
    lm.stufe("os.vm.tlb", 4)
    konzepte = json.loads((tlb / "learner" / "konzepte.json").read_text())
    konzepte["os.vm.tlb"].pop("pflicht_termin")  # simuliert: Termin ging verloren
    (tlb / "learner" / "konzepte.json").write_text(json.dumps(konzepte))
    aus = hook("stop_check.py", {"session_id": "s1", "last_assistant_message": "Gut, weiter."})
    assert "Wiederholungspflicht" in blockiert(aus)


def test_t6_mit_termin_kein_block(tlb):
    lm.stufe("os.vm.tlb", 4)
    assert hook("stop_check.py", {"session_id": "s1", "last_assistant_message": "Gut, weiter."}) is None
