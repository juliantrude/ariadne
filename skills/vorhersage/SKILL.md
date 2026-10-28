---
name: vorhersage
description: Vorhersage-Experiment für Low-Level-Themen – Code oder Messung vorlegen, Vorhersage festhalten, ausführen, vergleichen. Nutze diesen Skill, wenn sich eine Frage durch Ausführen beantworten lässt.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
Die Maschine widerlegt, nicht du.

1. Kleines, eigenständiges Programm oder Messkommando vorlegen (Datei im Sitzungsordner `sitzungen/<heute>/`).
2. Vorhersage verlangen: Was kommt heraus, und warum? Konkret (Zahlen, Größenordnung, welche Variante schneller).
3. Festhalten: `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" run vorhersage "<Vorhersage des Lernenden, wörtlich>"`
4. Ausführen lassen oder ausführen: `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" run <datei.c|.py|.sh>` bzw. `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" run -- <befehl>`.
5. Vergleich vom Lernenden erklären lassen. Auf das Ergebnis mit `⟦lauf: rN⟧` verweisen.
   Passt es nicht: Stufe 1 der Hinweisleiter („Was müsste stimmen, damit …?“), keine Erklärung vorweg.
Hinweis: run.py hat keine Sandbox. Nur eigenen, harmlosen Code ausführen. Für perf ggf. `kernel.perf_event_paranoid` (Entscheidung des Lernenden).
