# Auditor v1 stop and v2 repair

The single candidate invocation completed and retained `candidate_raw.json`. The first independent audit invocation stopped before emitting a verdict: its claim checker sent a valid incomplete schedule prefix to a helper that required every event in the full schedule, raising `ValueError: not a complete schedule`. The original `audit.py`, stdout, and stderr remain unchanged.

`audit_v2.py` is a separately hashed successor. Its only semantic repair is a prefix replay helper that validates unique event IDs and prerequisite order without requiring the prefix to contain all remaining events. It reads the original frozen model and candidate raw output, imports no candidate code, and preserves the first candidate result. No candidate rerun occurred.
