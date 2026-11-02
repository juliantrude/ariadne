# Ariadne – Entwicklung des Plugins

Dieses Repo ist der **Code** von Ariadne als Claude-Code-Plugin. Lerndaten liegen nie hier,
sondern in einem eigenen Lern-Repo (Verzeichnis mit `ariadne.toml`, angelegt mit `bin/ariadne einrichten`).
Die Hooks wirken nur in Lern-Repos; hier schweigen sie.

- `regeln.md` – Tutor-Regeln, eingespielt vom SessionStart-Hook. Das ist der frühere Inhalt der CLAUDE.md des Tutors.
- `skills/` – Skills, aufrufbar als `/ariadne:<name>`. Werkzeuge immer über `"${CLAUDE_PLUGIN_ROOT}/bin/ariadne" <werkzeug>`.
- `hooks/` – `hooks.json` und die Hook-Skripte. `register.tsx` ist ein Mod und zeichnet das Startband über der Eingabe (Test: `claude plugin test .`).
- `tools/` – CLI-Werkzeuge, Logik in `tools/kern/`. Das Dashboard rechnet in `kern/uebersicht.py` und schreibt in `kern/dashboard.py` Markdown für md-dashboard. Datenwurzel: `ARIADNE_ROOT`, sonst aufwärts nach `ariadne.toml`.
- `vorlage/` – Inhalt eines neuen Lern-Repos.
- `konzept/` – Konzept-PDF; jede Regel muss sich darauf zurückführen lassen.

Tests: `uv run pytest`. Zahlen (Aufwand, Termine, Bestehen, Beherrschung) gehören in Code, nie in Prompts.
Zum Ausprobieren ohne Installation: `claude --plugin-dir <pfad-zu-diesem-repo>` in einem Lern-Repo.
Nach Änderungen an einer installierten Version: Version in `.claude-plugin/plugin.json` erhöhen, dann `claude plugin update ariadne@juliantrude`.
