---
name: einlesen
description: Neues Kursmaterial (PDF) einlesen, in Seitentexte zerlegen und Konzepte mit Voraussetzungen vorschlagen. Nutze diesen Skill, wenn der Lernende ein Skript, eine Altklausur oder ein Paper hinzufügt.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
1. Die Datei muss unter material/ liegen (z. B. `material/os/skript.pdf`). Sonst bitten, sie dorthin zu kopieren.
   Vorher kurz erinnern: Darf das Material an einen externen Dienst gehen (Hochschulregeln, Urheberrecht)? Keine bewerteten Abgaben.
2. `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" ingest <pfad>` – meldet Seitenzahl und nicht prüfbare Seiten (Scans, Formelseiten).
3. Seitentexte in `material/.text/<dok>/` lesen (bei langen Skripten Inhaltsverzeichnis zuerst, dann kapitelweise).
4. Konzepte vorschlagen, als Tabelle: id (`kurs.bereich.konzept`), Titel, Voraussetzungen, Quelle (`datei.pdf#S12`).
   Feinkörnig genug, dass ein Konzept in einer Sitzung lernbar ist; grob genug, dass es nicht hunderte werden.
   Altklausuren: keine Konzepte, sondern als Prüfungsmaterial merken.
5. Erst nach Bestätigung (Änderungen übernehmen) anlegen, Voraussetzungen zuerst:
   `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" lm anlegen <id> "<Titel>" --quelle <q> --vor <id> ...`
6. Vorschlagen: `/ariadne:kapitel`, falls dieses Material zu einem neuen Lernvorhaben gehört.
