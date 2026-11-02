---
name: dashboard
description: Öffnet das Web-Dashboard mit Lernstand – Beherrschungsstufen je Bereich und Kapitel, Schwächen, Plan, Termine, Lernzeit, Kalibrierung. Aktualisiert sich selbst. Nutze diesen Skill, wenn der Lernende seinen Überblick im Browser sehen will.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
1. `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" dashboard` im Hintergrund starten (`run_in_background`). Er läuft weiter, bis er beendet wird, und aktualisiert sich selbst.
2. Die Adresse aus der Ausgabe nennen. Meldet das Werkzeug, dass md-dashboard fehlt, die Meldung weitergeben und auf die README verweisen.
3. Das Dashboard nicht deuten und keine Zahlen daraus wiederholen, solange der Lernende nicht danach fragt.
