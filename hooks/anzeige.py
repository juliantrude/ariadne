"""MessageDisplay: zeigt eine Antwort erst, wenn der Stop-Hook sie freigegeben hat (siehe kern/anzeige.py)."""
import json
import sys

from _pfad import DATEN, aus, ereignis

if aus():
    sys.exit(0)

from kern import anzeige  # noqa: E402

print(json.dumps({"hookSpecificOutput": {"hookEventName": "MessageDisplay",
                                         "displayContent": anzeige.halte(ereignis(), DATEN)}},
                 ensure_ascii=False))
