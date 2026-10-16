# Saved-auditor version note

The candidate invocation is unchanged. `AUDIT.json` and `AUDIT_EXIT_CODE.txt` preserve the first saved-record auditor result (exit 1): all lifecycle checks passed, but its exact-string comparison expected a bare commit SHA while the raw record included a descriptive `#7440 head ` / `#7429 head ` prefix. `audit_saved_v2.py` makes that comparison against the recorded suffix commit IDs, reruns only the saved-record audit, and writes `AUDIT-v2.json` / `AUDIT-v2_EXIT_CODE.txt`. No candidate or live operation was repeated.
