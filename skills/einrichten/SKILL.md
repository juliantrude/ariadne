---
name: einrichten
description: Ein neues Ariadne-Lern-Repo anlegen – eigenes Verzeichnis für Lernermodell, Material und Sitzungen, getrennt vom Plugin. Nutze diesen Skill, wenn jemand mit Ariadne anfangen will und noch kein Verzeichnis mit ariadne.toml hat.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" einrichten *)
---
1. Fragen, wo das Lern-Repo liegen soll. Vorschlag: ein Verzeichnis pro Person, nicht pro Kurs
   (das Lernermodell soll kursübergreifend wissen, was schon sitzt), z. B. `~/Documents/uni/ariadne`.
2. `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" einrichten <verzeichnis>`
3. Kurz erklären, was angelegt wurde, und auf `ariadne.toml` hinweisen: Dort steht, welche Teile
   des Claude-Gedächtnisses die Vorwissensanalyse lesen darf. Gesperrt sind standardmäßig Gesundheit,
   Camping und Garderobe. Bitten, das einmal anzusehen.
4. Hinweis: Ariadne wirkt nur in diesem Verzeichnis. Neue Claude-Code-Sitzung dort starten,
   dann `/ariadne:einlesen` für Material und `/ariadne:kapitel` für das erste Lernvorhaben.
