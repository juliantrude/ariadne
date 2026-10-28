"""PreToolUse: learner/ darf nur über `ariadne lm` und `ariadne plan` geändert werden (T5).

Schreibwerkzeuge werden am Zielpfad erkannt, Shell-Befehle an Schreiboperationen, deren
Ziel unter learner/ liegt. Das ist eine Leitplanke gegen Versehen, keine Sicherheitsgrenze.
"""
import json
import re
import shlex
import sys

from _pfad import DATEN, aus, ereignis

if aus():
    sys.exit(0)

GRUND = ("learner/ ist das Lernermodell und darf nur über `ariadne lm` bzw. `ariadne plan` geändert werden. "
         "Melde Beobachtungen (Stufe, Abruf, Vorwissen, Prüfungsitem) über diese Skripte.")
SCHREIBBEFEHLE = {"mv", "cp", "rm", "truncate", "touch", "install", "ln", "rsync", "dd", "chmod"}


def unter_learner(pfad: str) -> bool:
    if not pfad:
        return False
    try:
        (DATEN / pfad).resolve().relative_to((DATEN / "learner").resolve())
        return True
    except ValueError:
        return False


def shell_schreibt_learner(cmd: str) -> bool:
    if re.search(r"bin/ariadne\"?\s+(lm|plan)\b|tools/(lm|plan)\.py", cmd) and not re.search(r"[;&|>]", cmd):
        return False
    for ziel in re.findall(r">>?\s*([^\s;&|]+)", cmd) + re.findall(r"\btee\s+(?:-a\s+)?([^\s;&|]+)", cmd):
        if unter_learner(ziel):
            return True
    for teil in re.split(r"[;&|]+", cmd):
        try:
            worte = shlex.split(teil)
        except ValueError:
            worte = teil.split()
        if not worte:
            continue
        befehl = worte[0].rsplit("/", 1)[-1]
        ziele = [w.removeprefix("of=") for w in worte[1:]]
        if befehl in SCHREIBBEFEHLE and any(unter_learner(z) for z in ziele):
            return True
        if befehl == "sed" and any(w.startswith("-i") for w in worte) and any(unter_learner(z) for z in ziele):
            return True
        if befehl == "git" and len(worte) > 1 and worte[1] in ("checkout", "restore", "reset", "revert") \
                and any("learner" in w for w in worte):
            return True
        if befehl in ("python", "python3", "perl", "node", "ruby") and "-c" in worte[1:3] \
                and "learner" in teil:
            return True
    return False


ev = ereignis()
werkzeug, eingabe = ev.get("tool_name", ""), ev.get("tool_input", {}) or {}
verboten = False
if werkzeug in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
    verboten = unter_learner(eingabe.get("file_path") or eingabe.get("notebook_path") or "")
elif werkzeug == "Bash":
    verboten = shell_schreibt_learner(eingabe.get("command", ""))

if verboten:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": GRUND}}, ensure_ascii=False))
sys.exit(0)
