# MAP01 terminal-sync preflight successor #3211

This additive preflight does not rerun or consume allocation map01-recovery-cover-matched-live-v2-02.

## Frozen evidence

- #3202 run 35469191644, job 105966929823, artifact 10592561185.
- The first formal outcome was TimeoutError("session event timeout") while waiting for the recovery fallback terminal.
- The retained artifact contains only the completed pair-01 coast arm; its target pair1-coast_control-fallback has exactly one terminal event.
- The incomplete recovery arm is not silently treated as PASS.

## H/T/D/C/U

- H: terminal cardinality is an auditable boundary; exactly one matching terminal is required.
- T: run the standard-library audit over retained event JSONL and independent missing/duplicate/exactly-once controls in a python:3.12-slim container.
- D: PASS_TERMINAL_EVENT_ONCE only for a specific observed event stream; FAIL_TERMINAL_EVENT_PROTOCOL for missing or duplicate terminals. This preflight cannot classify the missing recovery stream.
- C: this tests event cardinality only; it does not repair session synchronization or authorize a new formal allocation.
- U: the recovery-arm timeout cause remains unresolved until a fresh additive diagnostic captures its live event trace.

Container command:
python -m unittest -v test_audit.py
python audit.py EVENTS.jsonl TARGET_ID
