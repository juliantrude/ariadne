---
name: wiederholen
description: Fällige Konzepte aus dem FSRS-Plan gemischt abfragen. Nutze diesen Skill zu Sitzungsbeginn, wenn Wiederholungen fällig sind, oder wenn der Lernende wiederholen will.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
1. `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" review` – fällige Konzepte. Reihenfolge mischen, Themen verschränken.
2. Pro Konzept eine Abruffrage (Anwendung, nicht Definition; nicht wörtlich dieselbe wie zuletzt). Immer erst Sicherheit 1–5, dann Antwort.
3. Bei Fehlern Hinweisleiter wie beim Lernen, Stufen mit `ariadne lm stufe` melden.
4. Ergebnis: `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" lm abruf <konzept> --richtig|--falsch --sicherheit S [--erklaerung-traegt nein]`
5. Am Ende: Anzahl, Trefferquote, Kalibrierung dieser Runde in einem Satz. Kein Wiederlesen als Ersatz für Abruf.
