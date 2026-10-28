"""M1: PDF -> Seitentexte; leere Seiten werden als nicht prüfbar erkannt."""
import json
import shutil

import pytest

from kern.quellen import pruefe_zitate

pytestmark = pytest.mark.skipif(not shutil.which("pdftotext"), reason="pdftotext fehlt")


def mini_pdf(seiten: list[list[str]]) -> bytes:
    """Ein minimales PDF mit Helvetica-Textzeilen pro Seite; leere Liste = leere Seite (wie ein Scan)."""
    objekte = ["<< /Type /Catalog /Pages 2 0 R >>", None,
               "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kinder = []
    for zeilen in seiten:
        befehle = "BT /F1 11 Tf 14 TL 50 780 Td " + " ".join(
            "(" + z.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") '" for z in zeilen) + " ET"
        objekte.append(f"<< /Length {len(befehle)} >>\nstream\n{befehle}\nendstream")
        inhalt = len(objekte)
        objekte.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                       f"/Resources << /Font << /F1 3 0 R >> >> /Contents {inhalt} 0 R >>")
        kinder.append(f"{len(objekte)} 0 R")
    objekte[1] = f"<< /Type /Pages /Kids [{' '.join(kinder)}] /Count {len(kinder)} >>"
    raus, offsets = b"%PDF-1.4\n", []
    for i, o in enumerate(objekte, 1):
        offsets.append(len(raus))
        raus += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(raus)
    raus += f"xref\n0 {len(objekte) + 1}\n0000000000 65535 f \n".encode()
    raus += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    raus += f"trailer\n<< /Size {len(objekte) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return raus


def test_m1_einlesen_und_zitieren(repo):
    import ingest

    fuell = ["Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor."] * 4
    pdf = repo / "material" / "os" / "skript.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(mini_pdf([fuell + ["The TLB caches recent virtual-to-physi-", "cal translations."] + fuell,
                              [], fuell + ["A TLB miss is handled by walking the page table."] + fuell]))
    d = ingest.einlesen(pdf)
    assert d["pfad"] == "os/skript.pdf" and d["seiten"] == 3 and d["leer"] == [2]
    index = json.loads((repo / "material" / ".text" / "index.json").read_text())
    assert "os-skript" in index["dokumente"]

    fehler, _ = pruefe_zitate('⟦"caches recent virtual-to-physical translations" | skript.pdf S. 1⟧ '
                              '⟦"walking the page table" | skript.pdf S. 3⟧')
    assert fehler == []
    fehler, _ = pruefe_zitate('⟦"walking the page table" | skript.pdf S. 2⟧')
    assert fehler[0].startswith("nicht prüfbar")
