---
name: meilenstein
description: Meilensteinprüfung eines Kapitels durchführen – Zwischenprüfung (gemischter Abruf ohne Hilfe) oder Challenge mit Kriterien – und das Ergebnis messbar festhalten. Nutze diesen Skill, wenn ein Meilenstein fällig ist oder der Lernende sich bereit fühlt.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
Prüfung, kein Unterricht: keine Hilfe, keine Hinweise, keine Rückmeldung bis zur Auswertung.

1. `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan status <id>` – welcher Meilenstein, welche Konzepte bzw. Kriterien.
   Steht er noch im Nebel, zuerst mit `/ariadne:plan` schärfen.
   Ankündigen: Umfang, Dauer (etwa 2–3 Minuten pro Frage), Bestehensgrenze, keine Hilfe.
2. `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan pruefung-start <id> <M>`
3. **Zwischenprüfung:** pro Konzept eine neue Abruffrage (nicht dieselbe wie beim Lernen), Reihenfolge gemischt, Konzepte verschränkt.
   Anwendung und Übertragung statt Definition. Wenn möglich Altklausur-Stil aus material/.
   **Challenge:** Aufgabe stellen, Lernenden arbeiten lassen; bei Low-Level-Aufgaben Vorhersage und Lauf über `ariadne run`.
4. Pro Item: erst Sicherheit 1–5, dann Antwort. Danach still bewerten und melden:
   `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan item <id> <M> --konzept <k> --ergebnis <richtig|teilweise|falsch> --sicherheit S`
   bzw. `--kriterium "<Kriterium>"` bei Challenges. Streng am Lösungsweg bewerten, nicht an der Person.
5. `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan auswerten <id> <M>`
6. **Rückmeldung:** Quote, bestanden ja/nein (so wie `ariadne plan` es sagt), pro schwachem Konzept die richtige Lösung mit Beleg
   und eine Selbsterklärungsfrage. Kalibrierung ansprechen: Wo war die Sicherheit hoch und die Antwort falsch?
   Nicht bestanden: schwache Konzepte als nächste `/ariadne:lernen`-Ziele, neuer Versuch in einigen Tagen; liegt der Plan dadurch zurück, `/ariadne:plan`.
   Danach `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan status <id>` zeigen.
