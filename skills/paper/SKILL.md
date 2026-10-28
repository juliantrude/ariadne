---
name: paper
description: Forschungsmodus – ein Paper aus material/ in drei Durchgängen sezieren, mit kritischer Prüfung. Nutze diesen Skill, wenn der Lernende ein Paper verstehen oder bewerten will. Keine Literatursuche.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
Literatursuche gehört nicht dazu (dafür Google Scholar, Zotero). Das Paper muss in material/ liegen und eingelesen sein.
In jedem Schritt liefert der Lernende zuerst seine Einschätzung; du gibst Rückfragen, dann Hinweise.

1. **Überblick (5–10 min):** Titel, Abstract, Einleitung, Überschriften, Fazit. Fragen: Welche Art Paper? Welche Behauptung? Bezug zum Kurs? Weiterlesen?
2. **Inhalt:** Abbildungen, Tabellen, Methodik. Pro Abbildung: „Was zeigt die y-Achse, und wie sähe es aus, wenn die Hypothese falsch wäre?“
3. **Kritische Prüfung** als Checkliste, je Punkt erst Rückfrage:
   Fragestellung und Hypothese (vorab festgelegt?) · Design (Randomisierung, Kontrolle, Stichprobe, Ausfälle) · Messung (misst es, was behauptet wird?) ·
   Statistik (Effektstärken, Konfidenzintervalle, Mehrfachvergleiche, Deckeneffekte) · Aussagekraft intern/extern · Reproduzierbarkeit · Bedeutung für das eigene Thema.
4. Ergebnis: Zusammenfassung **in den Worten des Lernenden**, mit geprüften Zitaten. Du korrigierst, schreibst aber nicht.
