"""Nur die geprüfte Fassung erscheint: MessageDisplay hält zurück, Stop entscheidet."""
import json
import subprocess
import sys

import pytest
from conftest import HOOKS, blockiert, hook, seiten
from kern import anzeige

SEITE = "Lorem ipsum dolor sit amet. " * 10 + "A TLB miss is handled by walking the page table."
GUT = '⟦"A TLB miss is handled by walking the page table" | skript.pdf S. 1⟧'
SCHLECHT = '⟦"erfunden" | skript.pdf S. 1⟧'


def stapel(index: int, delta: str, final: bool, nachricht="m1") -> dict:
    return {"session_id": "s1", "message_id": nachricht, "index": index, "delta": delta, "final": final}


def ohne_warten(ev, repo):
    return anzeige.halte(ev, repo, fenster_s=0, frist_s=0)


def test_ohne_stop_erscheint_die_nachricht_ganz(repo):
    """Zwischentext vor einem Werkzeugaufruf: Stop meldet sich nie."""
    assert ohne_warten(stapel(0, "eins\n", False), repo) == ""
    assert ohne_warten(stapel(1, "zwei\n", False), repo) == ""
    assert ohne_warten(stapel(2, "drei", True), repo) == "eins\nzwei\ndrei"


def test_stapel_duerfen_ungeordnet_ankommen(repo):
    assert ohne_warten(stapel(1, "zwei\n", False), repo) == ""
    assert ohne_warten(stapel(0, "eins\n", False), repo) == ""
    assert ohne_warten(stapel(2, "drei", True), repo) == "eins\nzwei\ndrei"


@pytest.mark.parametrize("zeigen", [True, False])
def test_das_urteil_von_stop_entscheidet(repo, zeigen):
    anzeige.stop_beginnt(repo, "s1", "Antwort\n")
    anzeige.stop_entscheidet(repo, "s1", "Antwort", zeigen)
    assert ohne_warten(stapel(0, "Antwort", True), repo) == ("Antwort" if zeigen else "")


def test_ohne_urteil_erscheint_die_nachricht_nach_der_frist(repo):
    anzeige.stop_beginnt(repo, "s1", "Antwort")
    assert ohne_warten(stapel(0, "Antwort", True), repo) == "Antwort"


def test_gleicher_text_spaeter_erbt_kein_altes_urteil(repo):
    anzeige.stop_beginnt(repo, "s1", "Antwort")
    anzeige.stop_entscheidet(repo, "s1", "Antwort", False)
    assert ohne_warten(stapel(0, "Antwort", True), repo) == ""
    assert ohne_warten(stapel(0, "Antwort", True, "m2"), repo) == "Antwort"


def anzeigen_parallel(ev):
    """Startet den Anzeige-Hook, der dann wie in Claude Code neben dem Stop-Hook läuft."""
    p = subprocess.Popen([sys.executable, str(HOOKS / "anzeige.py")], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, text=True)
    p.stdin.write(json.dumps(ev))
    p.stdin.close()
    return p


def angezeigt(prozess) -> str:
    aus = prozess.stdout.read()
    assert prozess.wait(timeout=30) == 0
    return json.loads(aus)["hookSpecificOutput"]["displayContent"]


@pytest.mark.parametrize("text, gezeigt", [(SCHLECHT, ""), (GUT, GUT)])
def test_beide_hooks_zusammen(repo, text, gezeigt):
    seiten(repo, "skript.pdf", [SEITE])
    p = anzeigen_parallel(stapel(0, text, True))
    aus = hook("stop_check.py", {"session_id": "s1", "last_assistant_message": text})
    assert bool(blockiert(aus)) == (not gezeigt)
    assert angezeigt(p) == gezeigt


def test_nach_der_letzten_runde_erscheint_die_antwort_mit_warnung(repo):
    seiten(repo, "skript.pdf", [SEITE])
    start = {"session_id": "s1", "last_assistant_message": SCHLECHT}
    for runde in (False, True):
        hook("stop_check.py", {**start, "stop_hook_active": runde})
        assert ohne_warten(stapel(0, SCHLECHT, True), repo) == ""
    p = anzeigen_parallel(stapel(0, SCHLECHT, True))
    aus = hook("stop_check.py", {**start, "stop_hook_active": True})
    assert aus["systemMessage"].startswith("⚠ Beleg prüfen")
    assert angezeigt(p) == SCHLECHT
