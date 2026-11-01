"""Liest, was Claude Code bereits über den Lernenden weiß (Agent Memory), für die Vorwissensanalyse.

Nur lesend. Ariadne schreibt kein Claude-Gedächtnis: Lernstand gehört ins Lernermodell,
wo er an Regeln und Git-Historie hängt (Abschnitt 5.8).
"""
from __future__ import annotations

import fnmatch
import glob
import os
import re
from pathlib import Path

from kern.basis import konfig

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.S)


def _meta(text: str) -> tuple[dict, str]:
    m = FRONTMATTER.match(text)
    if not m:
        return {}, text
    meta = {}
    for zeile in m.group(1).splitlines():
        if ":" in zeile:
            k, v = zeile.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, m.group(2)


def _projekt(pfad: Path) -> str:
    """~/.claude/projects/-home-name-Documents-uni/memory/x.md -> Documents-uni"""
    teile = pfad.parts
    if "projects" in teile:
        roh = teile[teile.index("projects") + 1]
        return re.sub(r"^-home-[^-]+-", "", roh)
    return pfad.parent.name


def eintraege() -> list[dict]:
    cfg = {"quellen": ["~/.claude/CLAUDE.md", "~/.claude/projects/*/memory/*.md"],
           "ausschliessen": [], "immer": ["user"], **konfig().get("gedaechtnis", {})}
    raus = []
    for muster in cfg["quellen"]:
        for datei in sorted(glob.glob(os.path.expanduser(muster))):
            p = Path(datei)
            if p.name == "MEMORY.md":
                continue
            if any(fnmatch.fnmatch(str(p.parent.parent), "*/" + a) or fnmatch.fnmatch(str(p), a)
                   for a in cfg["ausschliessen"]):
                continue
            meta, inhalt = _meta(p.read_text(errors="replace"))
            typ = meta.get("type", "user" if p.name == "CLAUDE.md" else "")
            raus.append({"datei": str(p), "projekt": _projekt(p), "name": meta.get("name", p.stem),
                         "beschreibung": meta.get("description", ""), "typ": typ,
                         "geaendert": meta.get("modified", ""), "inhalt": inhalt.strip(),
                         "immer": typ in cfg["immer"]})
    return raus


def relevante(stichworte: list[str]) -> tuple[list[dict], list[dict]]:
    """(immer gelesene Einträge, zum Thema passende weitere Einträge)."""
    alle = eintraege()
    muster = [re.compile(re.escape(s), re.I) for s in stichworte if s.strip()]
    immer = [e for e in alle if e["immer"]]
    passend = [e for e in alle if not e["immer"] and muster
               and any(m.search(e["inhalt"]) or m.search(e["beschreibung"]) or m.search(e["projekt"]) for m in muster)]
    return immer, passend


def als_markdown(stichworte: list[str], max_zeichen: int = 1500) -> str:
    immer, passend = relevante(stichworte)
    zeilen = ["# Was Claude bereits über den Lernenden weiß", "",
              "Quelle: Claude-Code-Gedächtnis, nur gelesen. Jede Angabe ist eine **Hypothese** über Vorwissen,",
              "kein Beleg. Beherrschung entsteht nur aus Diagnosefragen.", ""]
    for titel, gruppe in (("Über die Person (immer)", immer), (f"Zum Thema passend ({', '.join(stichworte)})", passend)):
        zeilen += [f"## {titel}", ""]
        if not gruppe:
            zeilen += ["(nichts gefunden)", ""]
        for e in gruppe:
            text = e["inhalt"] if len(e["inhalt"]) <= max_zeichen else e["inhalt"][:max_zeichen] + " …"
            zeilen += [f"### {e['name']}  ·  {e['projekt']}  ·  {e['typ'] or 'ohne Typ'}  ·  {e['geaendert'][:10]}",
                       f"_{e['beschreibung']}_" if e["beschreibung"] else "", "", text, "",
                       f"Ref: `{e['projekt']}/{e['name']}`", ""]
    return "\n".join(zeilen)
