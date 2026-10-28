---
name: kapitel
description: Ein neues Kapitel (Lernvorhaben) beginnen – Ziel klären, Kapitel anlegen, dann Vorwissensanalyse und verhandelten Lehrplan. Nutze diesen Skill, wenn der Lernende ein neues Thema, einen neuen Kurs oder eine neue Klausurvorbereitung anfangen will.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
Ein Kapitel startet nie direkt mit Inhalten. Reihenfolge ist fest: Ziel → Vorwissen → Plan → Lernen.

1. **Ziel klären** (kurz, eine Frage nach der anderen):
   - Worum geht es, und woran merkt man am Ende, dass es geschafft ist? (Klausur, Projekt, Verständnis)
   - Gibt es einen festen Termin? Datum genau erfragen.
   - Welches Material gibt es? Liegt es schon in material/ (`material/.text/index.json`)? Sonst erst `/ariadne:einlesen`.
2. **Konzepte festlegen.** Zeig die passenden Konzepte aus `learner/konzepte.json` (`"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" lm zeige <präfix>`).
   Fehlen welche, schlag sie vor (id, Titel, Voraussetzungen, Quelle) und lege sie erst nach Bestätigung mit `ariadne lm anlegen` an.
3. **Anlegen:**
   `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan neu <id> "<Titel>" --konzepte <präfix.|id,id> --ziel <art> --datum <JJJJ-MM-TT> --stichwort <Thema> ...`
   Stichworte = Begriffe, unter denen im Claude-Gedächtnis Vorwissen stehen könnte (Kursname, Modulnummer, Kernbegriffe).
4. Direkt weiter mit `/ariadne:vorwissen <id>`, danach `/ariadne:plan <id>`.
