---
name: karte
description: Lösungslandkarte für eine Aufgabe erstellen – Schlüsselstellen, Fehlvorstellungen, Zeitfallen, belegt aus dem Material. Wird von /ariadne:lernen vor der ersten Frage genutzt.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
Die Karte ist für dich, nicht für den Lernenden. Nicht vorlesen, nicht zitieren.

1. Aufgabe wählen, die das Konzept trägt (bei Vorwissen ein Problem, bei Beherrschung 0 ein ausgearbeitetes Beispiel mit Lücken).
2. Relevante Seiten aus `material/.text/` lesen.
3. Datei `.tutor/karten/<konzept>-<JJJJ-MM-TT>.yaml` schreiben:
   ```yaml
   aufgabe: "..."
   konzepte: [..]
   schluesselstellen:
     - id: S1
       einsicht: "..."
       beleg: ⟦"wörtliches Zitat" | datei.pdf S. n⟧
       zeitbudget_min: 8
   fehlvorstellungen:
     - text: "..."
       lehrreich: true          # zulassen, dann per Ausführung widerlegen
       aufloesung: "..."
   zeitfallen:
     - "..."                    # früh mit Stufe-2-Hinweis entschärfen
   ```
4. Jedes Zitat muss wörtlich auf der Seite stehen; der Stop-Hook prüft auch die Karte, sobald du daraus zitierst.
