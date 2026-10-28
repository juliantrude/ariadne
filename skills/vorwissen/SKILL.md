---
name: vorwissen
description: Vorwissensanalyse zu Beginn eines Kapitels – nutzt das Claude-Gedächtnis und das Lernermodell als Hypothesen und prüft sie mit kurzen Diagnosefragen. Nutze diesen Skill nach /ariadne:kapitel oder wenn der Startstand eines Kapitels unklar ist.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
Ziel: in 10–20 Minuten einen ehrlichen Startstand pro Konzept, damit der Plan auf echtem Vorwissen aufbaut.
Diagnose, nicht Unterricht: keine Hinweisleiter, keine Korrekturen. Fehlvorstellungen nur notieren.

1. **Was schon bekannt ist, zuerst lesen – das spart dem Lernenden Zeit:**
   - `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" gedaechtnis <stichworte des Kapitels>` – was Claude über die Person weiß
     (Studium, Vorkenntnisse, Projekte, Zeitbudget, Arbeitsweise).
   - `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" lm zeige` – Konzepte aus anderen Kapiteln mit Beherrschung.
   - `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan zeige <id>` – Ziel und Konzeptliste.
2. **Hypothesen bilden und offenlegen.** Sag in 3–6 Sätzen, was du aus dem Gedächtnis ableitest und woher
   („Laut deinem Uni-Gedächtnis hast du AuP bestanden, also vermute ich …“). Frag, ob etwas falsch oder veraltet ist.
   Merk dir die Refs der genutzten Einträge (`projekt/name` aus der Ausgabe).
   Zeitbudget und Belastung (Job, Training, Fristen) aus dem Gedächtnis gehören in die spätere Planverhandlung, nicht in die Diagnose.
3. **Selbsteinschätzung**, gruppiert statt einzeln: „Wie gut kennst du dich aus mit … (0 nie gehört – 4 könnte es erklären)?“
4. **Diagnosefragen** (je Konzept höchstens eine, insgesamt höchstens ~12):
   - Priorität: Voraussetzungen vor Folgekonzepten; Konzepte, bei denen Gedächtnis oder Selbsteinschätzung Vorwissen nahelegen.
   - Konzepte mit Selbsteinschätzung 0 und ohne Hinweis im Gedächtnis nicht abfragen → `uebersprungen`.
   - Fällt eine Voraussetzung durch, die darauf aufbauenden Konzepte nicht mehr abfragen → `uebersprungen`.
   - Fragen verlangen Anwenden oder Erklären, nicht Wiedererkennen. Keine Multiple Choice.
   - Immer zuerst Sicherheit 1–5, dann Antwort. Keine Rückmeldung zur Richtigkeit bis zum Ende.
   - Ergebnis melden:
     `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" lm vorwissen <konzept> <richtig|teilweise|falsch|uebersprungen> --sicherheit S --selbst N --kapitel <id> [--fehlvorstellung "…"]`
     richtig = korrekt und begründet; teilweise = Kern stimmt, Lücke oder unsichere Begründung.
5. **Abschließen:**
   `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan vorwissen-fertig <id> --zusammenfassung "<2–3 Sätze>" --gedaechtnis <ref> [--gedaechtnis <ref> ...]`
6. **Rückmeldung an den Lernenden:** Startstand pro Konzeptgruppe, Abstand zwischen Selbsteinschätzung und Ergebnis (Kalibrierung, ohne Wertung der Person),
   notierte Fehlvorstellungen nur benennen, nicht auflösen – das passiert beim Lernen. Dann weiter mit `/ariadne:plan <id>`.
