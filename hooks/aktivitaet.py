"""UserPromptSubmit: Zeitstempel für die gemessene Lernzeit."""
import sys

from _pfad import aus, ereignis

if aus():
    sys.exit(0)

from kern.zeit import melde_aktivitaet  # noqa: E402

melde_aktivitaet(ereignis().get("session_id", "ohne-sitzung"))
