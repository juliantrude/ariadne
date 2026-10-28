# Ariadne

Lernagent auf Basis von Claude Code: kennt den Weg, verrät ihn nicht.
Konzept und Begründung: `konzept/ariadne-lernagent-konzept.pdf`. Dieses Repo ist das Plugin, Version 0.2.

## Architektur

Ariadne ist ein Claude-Code-Plugin. Code und Lerndaten sind getrennt:

```
~/Work/ariadne/                 Plugin (dieses Repo): Regeln, Skills, Hooks, Werkzeuge
└─ installiert als Kopie nach ~/.claude/plugins/cache/ariadne/…  (der Tutor kann sie nicht nebenbei ändern)

<dein Lern-Repo>/               Daten, eigenes Git-Repo
├─ ariadne.toml                 Marker + persönliche Einstellungen
├─ .claude/settings.json        aktiviert das Plugin nur hier
├─ learner/ material/ sitzungen/ .tutor/karten/
```

Das Plugin ist für den Nutzer installiert, aber global deaktiviert. Jedes Lern-Repo aktiviert es in seinen
Projekteinstellungen. Zusätzlich schweigen die Hooks überall, wo keine `ariadne.toml` liegt.
Die Tutor-Regeln (`regeln.md`) spielt der SessionStart-Hook ein, weil ein Plugin keine CLAUDE.md mitbringen kann.

## Einrichten

```bash
# einmalig: Plugin aus dem lokalen Marktplatz installieren, global aus
claude plugin marketplace add ~/Work/ariadne
claude plugin install ariadne@ariadne --scope user
claude plugin disable ariadne@ariadne --scope user

# Lern-Repo anlegen (eins pro Person, kursübergreifend)
~/Work/ariadne/bin/ariadne einrichten ~/Documents/uni/ariadne
cd ~/Documents/uni/ariadne && claude
> /ariadne:einlesen material/os/skript.pdf
> /ariadne:kapitel
```

Voraussetzungen: Claude Code mit Abo, `uv`, `pdftotext` (poppler), `git`; für Low-Level-Experimente `gcc`, `gdb`, `perf`.

## Entwickeln

```bash
uv run pytest                                      # 60 Tests, ohne Modellaufruf
claude --plugin-dir ~/Work/ariadne                 # im Lern-Repo: Arbeitsstand ohne Installation testen
# Neue Version ausrollen: version in .claude-plugin/plugin.json erhöhen, dann
claude plugin marketplace update ariadne && claude plugin update ariadne@ariadne
```

## Ablauf

```
/ariadne:einrichten                  neues Lern-Repo
/ariadne:einlesen <pdf>              Material zerlegen, Konzepte bestätigen
/ariadne:kapitel                     neues Lernvorhaben: Ziel, Konzepte
  └ /ariadne:vorwissen               Gedächtnis + Lernermodell als Hypothesen, Diagnosefragen
  └ /ariadne:plan                    Lehrplan, Zeitplan verhandeln, vereinbaren; später Meilensteine schärfen
/ariadne:lernen <konzept>            Hinweisleiter, Lösungslandkarte, /ariadne:vorhersage
/ariadne:wiederholen                 FSRS, täglich
/ariadne:meilenstein <kapitel> <M>   Zwischenprüfung oder Challenge, messbar
/ariadne:fortschritt                 Ist gegen Soll, Rückstand in Tagen, Lernzeit
/ariadne:bilanz                      Wochenbilanz
/ariadne:klausur  /ariadne:paper     Klausursimulation, Forschungsmodus
```

## Neu gegenüber dem Konzept

**Vorwissensanalyse** (`/vorwissen`, `tools/gedaechtnis.py`). Liest nur lesend das Claude-Code-Gedächtnis
(`~/.claude/projects/*/memory`): Einträge über die Person immer, andere nur bei Treffer auf die Stichworte
des Kapitels. Gesperrte Projekte und Typen in `ariadne.toml`. Das Gedächtnis liefert Hypothesen und
bestimmt, *was* abgefragt wird. Den Startstand setzen nur Diagnosefragen, über feste Regeln in `lm.py`:
richtig → Beherrschung 2 (nie höher, Kompetenzillusion), teilweise → 1, falsch/übersprungen → 0.
Welche Gedächtniseinträge genutzt wurden, steht im Kapitel.

**Lehrplan mit verhandeltem Zeitplan** (`/plan`, `tools/plan.py`). Das Modell gliedert didaktisch in
Meilensteine, `plan.py` rechnet: Aufwand pro Konzept aus der Startbeherrschung, Zuschläge für
Wiederholung und Puffer, Termine aus Stunden pro Woche und aus der Energie (begrenzt neue Konzepte
pro Sitzung), Machbarkeit bis zum Zieldatum mit Hebeln (nötige Stunden, was bis zum Ziel passt).
Kein Plan ohne Vorwissensanalyse. Vereinbart ist ein Plan erst mit der wörtlichen Zustimmung des
Lernenden; `plan.py` und der Stop-Hook prüfen sie gegen das Gesprächsprotokoll.

**Meilensteine und messbarer Fortschritt** (`/meilenstein`, `/fortschritt`). Jeder Meilenstein hat eine
Prüfung: Zwischenprüfung (jedes Konzept ein Abruf ohne Hilfe) oder Challenge mit festen Kriterien,
bestanden ab Schwelle (Standard 80 %). Prüfungsitems zählen zugleich als Abruf im Lernermodell.
Nur der nächste Meilenstein ist scharf geplant. Spätere liegen im Nebel (Idee aus Matt Pococks Wayfinder):
Konzepte und Termine stehen, die Prüfung wird erst geschärft (`ariadne plan schaerfen`), wenn der vorige bestanden ist.
Fortschritt: Ist (aus Beherrschung, gewichtet mit Aufwand) gegen Soll (aus dem Plan), Rückstand in Tagen,
gemessene aktive Lernzeit gegen vereinbarte. Bei Rückstand ≥ 7 Tagen, verpasstem Meilenstein oder
< 60 % Lernzeit empfiehlt der SessionStart-Hook eine Neuverhandlung; bestandene Meilensteine bleiben erhalten.

## Aufbau des Plugins

```
.claude-plugin/             plugin.json, marketplace.json (lokaler Marktplatz)
regeln.md                   Tutor-Regeln, per SessionStart eingespielt
skills/                     14 Skills (/ariadne:<name>)
hooks/                      hooks.json: SessionStart, UserPromptSubmit (Lernzeit), PreToolUse (Schreibschutz), Stop (Prüfkette)
bin/ariadne                 ein Einstieg für alle Werkzeuge
tools/                      lm plan review run ingest gedaechtnis einrichten validiere_pruefer; Logik in tools/kern/
vorlage/                    Inhalt eines neuen Lern-Repos
konzept/                    Konzept-PDF
pruefer-validierung/        T7
```

## Stand der Tests

| Test | Stand |
|---|---|
| M1 PDF → Seitentexte, leere Seite erkannt | grün (`test_ingest`) |
| T1–T4 Zitatprüfung Ebene ① | grün |
| T5 Schreibschutz learner/ (Edit, Write, Shell) | grün |
| T6 Wiederholungspflicht nach Stufe 4 | grün |
| T7 Prüfer-Validierung | 5 Beispielpaare: 100 % erkannt, 0 % Fehlalarme (Haiku 5.5). **Offen:** 50 Paare aus echtem Material |
| T8 FSRS-Bewertung aus Hinweisstufe | grün |
| T9 Didaktik in 10 begleiteten Sitzungen | **offen** (M5) |
| T10 Transkript lesen | grün, Fixture im Format von Claude Code 2.1.304 |
| T11 Rekursion, max. zwei Korrekturrunden | grün; zusätzlich in einer echten Headless-Sitzung beobachtet |
| Vorwissen, Plan, Verhandlung, Meilensteine, Fortschritt, Lernzeit | grün (`test_planung`, `test_gedaechtnis`) |
| Plugin: Lern-Repo finden, einrichten, Hooks nur im Lern-Repo, Nebel-Meilensteine | grün (`test_plugin`); echte Sitzung: Regeln eingespielt, Skill als Slash-Befehl mit Werkzeugaufruf ohne Rückfrage |

## Grenzen dieser Version

- Lernzeit ist geschätzt aus Eingabe-Zeitstempeln (Pausen > 15 min zählen nicht) und nicht pro Kapitel getrennt.
- Die Aufwandsschätzung (`aufwand_min`) ist ein Startwert. Nach einigen Wochen gegen die gemessene Zeit nachjustieren.
- `run.py` hat keine Sandbox.
- Schreibschutz und Hooks sind Leitplanken gegen Versehen, keine Sicherheitsgrenze.
- Ruft das Modell einen Skill selbst über das Skill-Werkzeug auf, kam im Headless-Test der Inhalt nicht an; als Slash-Befehl funktioniert er. Die Regeln enthalten dafür einen Rückfallweg (SKILL.md direkt lesen). Im interaktiven Betrieb noch beobachten.
- Ob ein Meilenstein-Item richtig ist, beurteilt das Modell; bestanden oder nicht entscheidet die Schwelle in `plan.py`.
