# Prüfer-Validierung (T7)

`beispiele.jsonl` zeigt das Format mit fünf konstruierten Paaren. Für die echte Validierung
50 Paare aus dem eigenen Material in `paare.jsonl` anlegen, davon etwa 20 mit eingebauten Fehlern:
verdrehte Aussage, aus dem Kontext gerissenes Zitat, unbelegte und unmarkierte Aussage.

    uv run python tools/validiere_pruefer.py                      # Haiku
    uv run python tools/validiere_pruefer.py --modell claude-sonnet-5-5

Ziel: ≥ 90 % der Fehler erkannt („nein“ oder „unklar“), ≤ 20 % Fehlalarme.
Wird das verfehlt: Prompt (`tools/pruefer_prompt.md`) nachschärfen oder in `ariadne.toml` Sonnet als Standardprüfer setzen.
