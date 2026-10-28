"""Zeigt, was Claude Code schon über den Lernenden weiß – Grundlage der Vorwissensanalyse.
Aufruf: ariadne gedaechtnis STICHWORT [STICHWORT ...]
Nur lesend. Was gelesen wird, steuert ariadne.toml [gedaechtnis]."""
import sys

from kern.gedaechtnis import als_markdown

if __name__ == "__main__":
    print(als_markdown(sys.argv[1:]))
