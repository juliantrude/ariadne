---
name: bilanz
description: Wochenbilanz – Konzepte nach Beherrschung, Kalibrierung, Hinweisstufen, Notausgänge, Plan und Meilensteine. Reine Auswertung der Dateien. Nutze diesen Skill am Wochenende oder auf Wunsch.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
Reine Auswertung der Dateien, ohne Urteil über die Person.

1. Daten sammeln:
   - `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" lm zeige` – Beherrschung, offene Fehlvorstellungen.
   - `learner/kalibrierung.csv` der letzten 7 Tage: Trefferquote bei Sicherheit 4–5 und bei 1–2, Vergleich zur Vorwoche.
   - `sitzungen/*/protokoll.jsonl` der letzten 7 Tage: Ø Hinweisstufe, wie oft Stufe 4, wie oft Notausgang.
   - `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" review vorschau 7` – Wiederholungslast der nächsten Woche.
   - `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan status` – Plan, Meilensteine, gemessene Lernzeit.
   Zahlen mit einem kurzen Python-Einzeiler über die Dateien berechnen, nicht schätzen.
2. Ausgabe im Format:
   ```
   /ariadne:bilanz Woche NN
   Konzepte: N gesamt · a sicher (4) · b im Aufbau (2–3) · c neu (0–1)
   Wiederholung: x fällig, y erledigt · Trefferquote z %
   Kalibrierung: Sicherheit 4–5 → p % richtig (Vorwoche q %) · Sicherheit 1–2 → r % richtig
   Hinweisstufen: Ø s · Stufe 4 erreicht: k× · Notausgang: m×
   Plan <kapitel>: Ist i % / Soll j % · d Tage voraus/zurück · Lernzeit t von v min · nächster Meilenstein Mx am …
   Offene Fehlvorstellungen: …
   ```
3. Eine Empfehlung für die nächste Woche, abgeleitet aus den Zahlen. Bei Neuverhandlungsgrund: `/ariadne:plan` anbieten.
