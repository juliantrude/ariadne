"""T1 im Hook, T10 Transkript, T11 Rekursion und Korrekturrunden, Prüferlogik, SessionStart."""
import json
from pathlib import Path

from conftest import hook, seiten, transkript
from kern import pruefer
from kern.transkript import letzte_antwort, nutzer_eingaben

FIXTURE = Path(__file__).parent / "fixtures" / "transkript_2_1.jsonl"
SEITE = "Lorem ipsum dolor sit amet. " * 10 + "A TLB miss is handled by walking the page table." + " Lorem ipsum." * 10


def test_t10_letzte_antwort_aus_gespeichertem_transkript():
    assert letzte_antwort(FIXTURE) == 'Ich schaue nach.\n⟦"caches recent translations" | skript.pdf S. 2⟧'
    assert nutzer_eingaben(FIXTURE) == ["Was ist ein TLB?", "Okay, das passt so für mich."]


def test_t1_im_stop_hook_mit_transkript(repo, tmp_path):
    seiten(repo, "skript.pdf", [SEITE])
    t = transkript(tmp_path / "t.jsonl", [("user", "Frage"), ("assistant", '⟦"TLB stores data" | skript.pdf S. 1⟧')])
    aus = hook("stop_check.py", {"session_id": "s1", "transcript_path": str(t)})
    assert aus["decision"] == "block" and "Zitat nicht gefunden" in aus["reason"]


def test_echtes_zitat_geht_durch(repo):
    seiten(repo, "skript.pdf", [SEITE])
    ev = {"session_id": "s1", "last_assistant_message": '⟦"A TLB miss is handled by walking the page table" | skript.pdf S. 1⟧'}
    assert hook("stop_check.py", ev) is None


def test_t11_pruefaufruf_loest_keine_hooks_aus(repo):
    ev = {"session_id": "s1", "last_assistant_message": '⟦"erfunden" | skript.pdf S. 1⟧'}
    for name in ("stop_check.py", "session_start.py", "guard_learner.py", "aktivitaet.py"):
        assert hook(name, ev, ARIADNE_PRUEFER="1") is None


def test_t11_hoechstens_zwei_korrekturrunden(repo):
    seiten(repo, "skript.pdf", [SEITE])
    ev = {"session_id": "s1", "last_assistant_message": '⟦"erfunden" | skript.pdf S. 1⟧'}
    assert hook("stop_check.py", {**ev, "stop_hook_active": False})["decision"] == "block"
    assert hook("stop_check.py", {**ev, "stop_hook_active": True})["decision"] == "block"
    dritte = hook("stop_check.py", {**ev, "stop_hook_active": True})
    assert "decision" not in dritte and dritte["systemMessage"].startswith("⚠ Beleg prüfen")
    # neue Nutzereingabe: Zähler beginnt von vorn
    assert hook("stop_check.py", {**ev, "stop_hook_active": False})["decision"] == "block"


def test_pruefer_eskaliert_bei_unklar(repo):
    aufrufe = []

    def falsch(modell, eingabe):
        aufrufe.append(modell)
        return {"gesamt": "unklar"} if modell == "claude-haiku-5-5" else {"gesamt": "nein", "aussagen": [
            {"text": "Moderne CPUs haben zwei TLB-Stufen", "stuetzt": "fehlt", "grund": "kein Beleg"}]}

    urteil = pruefer.pruefe("Antwort", [], rufe=falsch)
    assert aufrufe == ["claude-haiku-5-5", "claude-sonnet-5-5"] and urteil["modell"] == "claude-sonnet-5-5"
    assert pruefer.befunde(urteil) == ['fehlt: "Moderne CPUs haben zwei TLB-Stufen" – kein Beleg']


def test_pruefer_json_robust():
    assert pruefer._json_aus('Hier: {"aussagen": [], "gesamt": "ja"} fertig')["gesamt"] == "ja"
    assert pruefer._json_aus("kein json") is None
    assert pruefer._json_aus('{"gesamt": "vielleicht"}') is None


def test_kurze_rueckfrage_kostet_keinen_pruefer():
    assert not pruefer.enthaelt_fachaussagen("Was steht in einem TLB-Eintrag? Wie sicher bist du, 1 bis 5?")
    assert pruefer.enthaelt_fachaussagen("Kurz: ⟦unbelegt⟧ Das ist so.")


def test_session_start_meldet_sitzung_und_lage(repo, tmp_path):
    env_datei = tmp_path / "env"
    aus = hook("session_start.py", {"session_id": "abc", "transcript_path": "/x.jsonl"},
               CLAUDE_ENV_FILE=str(env_datei), ARIADNE_SESSION="")
    assert "export ARIADNE_SESSION=abc" in env_datei.read_text()
    assert (repo / "sitzungen" / ".aktuell").read_text() == "abc"
    assert "/ariadne:kapitel" in aus["hookSpecificOutput"]["additionalContext"]


def test_aktivitaet_wird_gemessen(repo):
    hook("aktivitaet.py", {"session_id": "s1"})
    zeilen = (repo / "sitzungen" / "2026-11-02" / "aktivitaet.jsonl").read_text().splitlines()
    assert json.loads(zeilen[0])["sitzung"] == "s1"
