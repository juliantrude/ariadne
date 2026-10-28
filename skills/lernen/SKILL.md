---
name: lernen
description: Ein Konzept im Klausurmodus erarbeiten, mit Lösungslandkarte und Hinweisleiter. Nutze diesen Skill, wenn der Lernende ein Konzept neu lernen oder vertiefen will.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
1. Lies `learner/konzepte.json` für das Konzept und seine Voraussetzungen (`"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" lm zeige <präfix>`).
   Voraussetzung mit Beherrschung < 2 → zuerst diese wiederholen.
   Gehört das Konzept zu einem Kapitel, kurz den Planstand nennen (`"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan status <kapitel>`): Meilenstein, Zieldatum.
   Neue Konzepte pro Sitzung höchstens `neue_pro_sitzung` aus dem Plan.
2. Beherrschung 0 → mit ausgearbeitetem Beispiel und Selbsterklärungsfragen beginnen. Sonst → mit einem Problem beginnen.
   Fehlvorstellungen aus der Vorwissensanalyse (im Konzept unter `fehlvorstellungen`) gezielt provozieren.
3. Erstelle mit `/ariadne:karte` die Lösungslandkarte, bevor du die erste Frage stellst.
4. Arbeite die Schlüsselstellen der Reihe nach ab, mit der Hinweisleiter aus CLAUDE.md.
   Nach jeder Schlüsselstelle: `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" lm stufe <konzept> <0-4> --stelle S<n>`. Bei Low-Level-Themen `/ariadne:vorhersage` verwenden.
   Behobene Fehlvorstellung: `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" lm fehlvorstellung <konzept> "<text>" --behoben`.
5. Am Ende: ein Abruftest ohne Hilfe zu jeder Schlüsselstelle (Sicherheit zuerst), Ergebnis:
   `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" lm abruf <konzept> --richtig|--falsch --sicherheit S [--erklaerung-traegt nein] [--schnell]`
   Die Stufe nimmt `ariadne lm` aus dem Sitzungsprotokoll. Danach kurz: was als Nächstes im Plan steht.
