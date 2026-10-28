---
name: plan
description: Lehrplan mit Meilensteinen und Zeitplan für ein Kapitel erstellen und mit dem Lernenden verhandeln, auch neu verhandeln, wenn er zurückliegt oder sich etwas ändert. Nutze diesen Skill nach /ariadne:vorwissen, bei "Neuverhandlung empfohlen" oder wenn der Lernende Zeit, Energie oder Ziel ändern will.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
Du gliederst didaktisch und verhandelst. `ariadne plan` rechnet Aufwand, Termine und Machbarkeit. Rechne nie selbst nach oder um.

1. **Ausgangslage:** `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan status <id>` und bei Neuverhandlung den Grund nennen (Rückstand, verpasster Meilenstein, zu wenig Lernzeit), ohne Vorwurf.
2. **Budget erfragen**, offen und realistisch – nicht, was ideal wäre, sondern was in einer normalen Woche geht:
   - Stunden pro Woche, Zahl der Sitzungen, typische Tageszeit.
   - Energie: niedrig / mittel / hoch. Sie bestimmt, wie viele neue Konzepte pro Sitzung kommen (Arbeitsgedächtnis).
   - Bekannte Engpässe (Abgaben, Prüfungen, Urlaub). Was im Gedächtnis zu Job, Training oder Fristen steht, ansprechen statt ignorieren.
3. **Gliederung entwerfen:** 2–6 Meilensteine, je ein zusammenhängender Block (Voraussetzungen zuerst), je 1–3 Wochen.
   **Nur der erste Meilenstein wird scharf geplant**, mit messbarer Prüfung:
   - `zwischenpruefung`: gemischter Abruf ohne Hilfe, jedes Konzept einmal. Standard.
   - `challenge`: praktische Aufgabe mit 2–5 beobachtbaren `kriterien` (z. B. „Vorhersage begründet“, „Messung reproduziert“, „Altklausuraufgabe 3 gelöst“).
   Optional eigene `schwelle` (Standard 0.8).
   **Spätere Meilensteine liegen im Nebel:** Konzepte und Termin stehen (sonst gäbe es keinen Zeitplan),
   die Prüfung ist nur eine Skizze (`beschreibung`). Geschärft wird sie, wenn der vorige bestanden ist –
   dann weiß man, was wirklich sitzt, und plant nicht auf Annahmen, die sich als falsch erweisen.
   Als JSON-Datei in `sitzungen/<heute>/gliederung-<id>.json`:
   `[{"titel": "...", "konzepte": [...], "pruefung": {"art": "challenge", "beschreibung": "...", "kriterien": [...]}}, {"titel": "...", "konzepte": [...], "pruefung": {"beschreibung": "Skizze"}}]`
4. **Rechnen lassen:**
   `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan vorschlag <id> --stunden H --sitzungen N --energie E --gliederung <datei> [--notiz "Grund"]`
5. **Verhandeln.** Zeig Meilensteine mit Zieldaten, Gesamtaufwand und Machbarkeit. Bei „nicht machbar“ die Hebel mit den Zahlen aus der Ausgabe anbieten:
   mehr Stunden (`noetige_stunden_pro_woche`), Umfang kürzen (`passt_bis_ziel`, was am wenigsten klausurrelevant ist), Ziel verschieben, oder mehr Energie/Sitzungen.
   Jede Änderung neu rechnen lassen. Auch ein machbarer Plan wird bestätigt, nicht vorausgesetzt: „Ist das realistisch für dich?“
   Plane lieber zu knapp als zu voll – ein Plan, der nach zwei Wochen gerissen ist, demotiviert.
6. **Vereinbaren** erst nach ausdrücklicher Zustimmung. Den Satz des Lernenden wörtlich übernehmen:
   `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan vereinbaren <id> --zustimmung "<sein Satz>"`
   Ohne klares Ja bleibt es ein Entwurf. Dann: nächster Schritt aus der Statusausgabe.
7. **Schärfen** (wenn der Status „schärfen“ als nächsten Schritt nennt): Ergebnis des bestandenen Meilensteins und
   aktuelle Beherrschung ansehen (`ariadne lm zeige`), Prüfung für den nächsten festlegen – schwache Konzepte des
   vorigen Versuchs dürfen mitgeprüft werden. Mit dem Lernenden kurz abstimmen, dann:
   `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan schaerfen <id> <M> --pruefung '<json>' [--titel "…"]`
   Passen Konzepte oder Termine nicht mehr, ist das keine Schärfung, sondern eine Neuverhandlung (Schritte 2–6).
