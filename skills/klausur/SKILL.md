---
name: klausur
description: Klausursimulation unter Zeitdruck, Themen gemischt, ohne Hilfe; Auswertung danach. Nutze diesen Skill zur Prüfungsvorbereitung oder wenn der Lernende sich testen will.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
1. Umfang und Zeit vereinbaren (z. B. 45 min, 4 Aufgaben). Bevorzugt Altklausuraufgaben aus material/, sonst eigene im Altklausurstil.
   Themen mischen; Konzepte aus mehreren Meilensteinen.
2. Während der Simulation: keine Hilfe, keine Hinweise, keine Rückmeldung. Notausgang heißt hier: Aufgabe abbrechen.
3. Pro Aufgabe Sicherheit 1–5 vor der Abgabe.
4. Auswertung danach: Punkte nach Lösungsweg, Musterlösung mit Belegen, Selbsterklärung zu jedem Fehler.
   Pro betroffenem Konzept: `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" lm abruf <konzept> --richtig|--falsch --sicherheit S --stufe 0 --quelle klausur`
5. Gibt es ein Kapitel mit Klausurziel: `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan status <id>` zeigen und einordnen.
