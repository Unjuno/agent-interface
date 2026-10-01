# Answer-surface denied-attempt successor

This is a fresh finite synthetic method successor to Issue #6173's retained `METHOD_FAIL_AUDIT`. It tests the confirmed candidate defect (denied attempts collapsed into no attempt) while avoiding the predecessor auditor's self-claim false positive. It does not read, change, or rerun predecessor files.

Run `python3 -B -m unittest -v test_protocol` first. After freezing `FREEZE.json`, run `python3 -B run_candidate.py` once, then `python3 -B run_audit.py` once only if the candidate exits 0. The candidate sees only `candidate_input.json`; the auditor uses observer-side `observer_trace.json` and imports no candidate module.

No real answer keys, model, user data, GitHub/web retrieval, or network are used. This is not a real benchmark-contamination finding or a completeness guarantee for production monitoring.
