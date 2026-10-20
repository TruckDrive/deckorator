# Kleines Fehlerprotokoll im Speicher (nichts wird gesendet oder auf Platte geschrieben).
# Landet nur im Diagnosebericht, den Nutzer selbst kopieren und weitergeben können.
import time
import traceback

ENTRIES = []
LIMIT = 20


def record(where, exc):
    tb = traceback.extract_tb(exc.__traceback__)
    place = f"{tb[-1].name}:{tb[-1].lineno}" if tb else ""
    ENTRIES.append(f"{time.strftime('%H:%M:%S')} {where}: {type(exc).__name__}: {exc} ({place})")
    del ENTRIES[:-LIMIT]
