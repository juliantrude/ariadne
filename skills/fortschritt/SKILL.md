---
name: fortschritt
description: Zeigt, wo der Lernende steht – Fortschritt gegen Plan, Meilensteine, gemessene Lernzeit, nächster Schritt. Nutze diesen Skill, wenn der Lernende fragt, wie weit er ist, ob er im Zeitplan liegt, oder zu Beginn einer Sitzung.
allowed-tools:
  - Bash("${CLAUDE_PLUGIN_ROOT}/bin/ariadne" *)
---
1. `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" plan status` (alle Kapitel) bzw. `status <id>`.
2. Die Ausgabe zeigen, wie sie ist. Dann in zwei, drei Sätzen einordnen: im Plan, voraus oder zurück (in Tagen), nächster Meilenstein und was bis dahin fehlt.
   Ist = Beherrschung aus beobachteten Abrufen, Soll = vereinbarter Plan, Lernzeit = gemessene aktive Zeit. Nichts davon schätzt du selbst.
3. Steht dort „Neuverhandlung empfohlen“, Grund nennen und `/ariadne:plan` anbieten. Nicht drängen, nicht beschönigen.
4. Nächsten Schritt aus der Ausgabe vorschlagen.
