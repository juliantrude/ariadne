"""Plugin-Aufbau: Lern-Repo finden, einrichten, Hooks nur im Lern-Repo, Nebel-Meilensteine."""
import json
import os
import subprocess
import sys

import pytest
from conftest import HOOKS, REPO

from kern import lernermodell as lm
from kern import planung as pl
from kern.basis import finde_lernrepo


def test_lernrepo_wird_aufwaerts_gefunden(tmp_path):
    (tmp_path / "ariadne.toml").write_text("")
    tief = tmp_path / "material" / "os"
    tief.mkdir(parents=True)
    assert finde_lernrepo(tief) == tmp_path
    assert finde_lernrepo(tmp_path.parent) is None


def test_einrichten_legt_lernrepo_an_und_ueberschreibt_nichts(tmp_path):
    import einrichten

    ziel = tmp_path / "lernen"
    ziel.mkdir()
    (ziel / "CLAUDE.md").write_text("meine Notizen")
    neu = einrichten.einrichten(ziel)
    assert "ariadne.toml" in neu and "CLAUDE.md" not in neu
    assert (ziel / "CLAUDE.md").read_text() == "meine Notizen"
    assert json.loads((ziel / ".claude" / "settings.json").read_text())["enabledPlugins"] == {"ariadne@juliantrude": True}
    assert (ziel / "learner" / "kapitel").is_dir() and (ziel / ".git").is_dir()
    with pytest.raises(SystemExit):
        einrichten.einrichten(ziel)


def test_hooks_schweigen_ausserhalb_eines_lernrepos(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("ARIADNE_")}
    for name in ("session_start.py", "stop_check.py", "guard_learner.py", "aktivitaet.py", "anzeige.py"):
        r = subprocess.run([sys.executable, str(HOOKS / name)], input=json.dumps(
            {"session_id": "x", "tool_name": "Write", "tool_input": {"file_path": "learner/x"},
             "last_assistant_message": '⟦"erfunden" | a.pdf S. 1⟧'}),
            capture_output=True, text=True, cwd=tmp_path, env={**env, "CLAUDE_PROJECT_DIR": str(tmp_path)})
        assert r.returncode == 0 and r.stdout == "", (name, r.stdout, r.stderr)
    assert not (tmp_path / "sitzungen").exists()


def test_session_start_spielt_regeln_ein(repo):
    from conftest import hook
    kontext = hook("session_start.py", {"session_id": "abc"})["hookSpecificOutput"]["additionalContext"]
    assert "Du bist Ariadne" in kontext and "${CLAUDE_PLUGIN_ROOT}" not in kontext
    assert f"{REPO}/bin/ariadne" in kontext


def test_wrapper_findet_werkzeug_im_lernrepo(repo):
    r = subprocess.run([str(REPO / "bin" / "ariadne"), "lm", "anlegen", "x.y", "Test"], capture_output=True,
                       text=True, cwd=repo / "material", env={k: v for k, v in os.environ.items() if k != "ARIADNE_ROOT"})
    assert r.returncode == 0, r.stderr
    assert "x.y" in json.loads((repo / "learner" / "konzepte.json").read_text())


@pytest.fixture
def plan_mit_nebel(repo):
    for kid, vor in [("a", []), ("b", ["a"]), ("c", ["b"]), ("d", ["c"])]:
        lm.anlegen(kid, kid.upper(), voraussetzungen=vor)
    pl.neu("k", "K", ["a", "b", "c", "d"], "klausur", None)
    pl.vorwissen_abschliessen("k", "neu", [])
    pl.vorschlag("k", 4, 2, "mittel", [
        {"titel": "AB", "konzepte": ["a", "b"], "pruefung": {"art": "zwischenpruefung"}},
        {"titel": "CD", "konzepte": ["c", "d"], "pruefung": {"art": "challenge", "beschreibung": "irgendwas mit perf"}}])
    pl.vereinbaren("k", "ok")
    return repo


def test_nur_der_erste_meilenstein_ist_scharf(plan_mit_nebel):
    m1, m2 = pl.lade("k")["plan"]["meilensteine"]
    assert m1["scharf"] and not m2["scharf"]
    assert m2["pruefung"] == {"art": "nebel", "schwelle": 0.8, "skizze": "irgendwas mit perf"}
    assert m2["zieldatum"] > m1["zieldatum"]  # Termine stehen trotzdem
    with pytest.raises(pl.Fehler, match="Nebel"):
        pl.pruefung_start("k", "M2")


def test_schaerfen_erst_nach_bestandenem_vorgaenger(plan_mit_nebel):
    challenge = {"art": "challenge", "beschreibung": "TLB messen", "kriterien": ["Vorhersage", "Messung"]}
    with pytest.raises(pl.Fehler, match="Erst M1"):
        pl.schaerfen("k", "M2", challenge)
    pl.pruefung_start("k", "M1")
    for k in ("a", "b"):
        pl.pruefung_item("k", "M1", "richtig", 4, konzept=k)
    pl.pruefung_auswerten("k", "M1")
    assert pl.status("k")["naechster_schritt"] == "/ariadne:plan k (M2 schärfen)"
    with pytest.raises(pl.Fehler, match="kriterien"):
        pl.schaerfen("k", "M2", {"art": "challenge"})
    m2 = pl.schaerfen("k", "M2", challenge, titel="TLB-Challenge")
    assert m2["scharf"] and m2["pruefung"]["kriterien"] == ["Vorhersage", "Messung"] and m2["pruefung"]["schwelle"] == 0.8
    assert pl.pruefung_start("k", "M2")["titel"] == "TLB-Challenge"
