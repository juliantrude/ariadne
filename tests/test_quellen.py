"""T1–T4: Ebene ① der Quellenprüfung, ohne Modell."""
from conftest import seiten
from kern.quellen import pruefe_laeufe, pruefe_zitate

FUELL = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 5
S1 = FUELL + "\nThe translation lookaside buffer caches recent virtual-to-physi-\ncal translations per page.\n" + FUELL
S2 = FUELL + "\nA TLB miss is handled by walking the page table.\n" + FUELL


def test_t1_erfundenes_zitat(repo):
    seiten(repo, "os/skript.pdf", [S1, S2])
    fehler, _ = pruefe_zitate('⟦"the TLB stores data" | skript.pdf S. 1⟧')
    assert fehler and fehler[0].startswith("Zitat nicht gefunden")


def test_t2_zitat_ueber_zeilenumbruch_mit_silbentrennung(repo):
    seiten(repo, "os/skript.pdf", [S1, S2])
    fehler, zitate = pruefe_zitate('So steht es: ⟦"caches recent virtual-to-physical translations" | skript.pdf S. 1⟧')
    assert fehler == []
    assert zitate[0]["seite"] == 1 and "lookaside" in zitate[0]["absatz"]


def test_t2b_typografische_anfuehrungszeichen_und_pfad(repo):
    seiten(repo, "os/skript.pdf", [S1, S2])
    fehler, _ = pruefe_zitate('⟦„A TLB miss is handled by walking the page table“ | os/skript.pdf S. 2⟧')
    assert fehler == []


def test_t3_seite_um_eins_verschoben(repo):
    seiten(repo, "os/skript.pdf", [S1, S2])
    fehler, _ = pruefe_zitate('⟦"A TLB miss is handled by walking the page table" | skript.pdf S. 1⟧')
    assert fehler == ['falsche Seite: "A TLB miss is handled by walking the page table" steht auf S. 2, nicht S. 1']


def test_t4_scanseite_nie_ok(repo):
    seiten(repo, "os/skript.pdf", [S1, "  \n Abb. 3 \n"])
    fehler, _ = pruefe_zitate('⟦"Abb. 3" | skript.pdf S. 2⟧')
    assert fehler and fehler[0].startswith("nicht prüfbar")


def test_unbekanntes_dokument(repo):
    fehler, _ = pruefe_zitate('⟦"irgendwas" | gibtsnicht.pdf S. 1⟧')
    assert fehler and "unbekannt" in fehler[0]


def test_lauf_muss_aus_dieser_sitzung_stammen(repo):
    runs = repo / "sitzungen" / "2026-11-02" / "runs"
    runs.mkdir(parents=True)
    (runs / "r1.json").write_text('{"sitzung": "andere"}')
    (runs / "r2.json").write_text('{"sitzung": "s1"}')
    assert pruefe_laeufe("⟦lauf: r2⟧", "s1") == []
    assert pruefe_laeufe("⟦lauf: r1⟧ ⟦lauf: r9⟧", "s1") == [
        "Lauf r1 existiert in dieser Sitzung nicht", "Lauf r9 existiert in dieser Sitzung nicht"]
