"""run.py: Vorhersage wird an den Lauf gebunden, Lauf ist als Beleg prüfbar."""
from kern.quellen import pruefe_laeufe


def test_vorhersage_und_lauf(repo):
    import run

    skript = repo / "x.py"
    skript.write_text("print(6 * 7)")
    vid = run.vorhersage("Es kommt 42 heraus")
    lauf = run.ausfuehren([str(skript)])
    assert lauf["schritte"][0]["stdout"].strip() == "42" and lauf["vorhersage"]["id"] == vid
    assert pruefe_laeufe(f"⟦lauf: {lauf['id']}⟧", "s1") == []
    zweiter = run.ausfuehren(["true"])
    assert zweiter["id"] == "r2" and zweiter["vorhersage"] is None
