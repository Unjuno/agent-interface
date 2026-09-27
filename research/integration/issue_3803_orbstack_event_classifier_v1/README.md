# Issue #3803 OrbStack saved-response event classifier

This bundle tests the event-count failure from the retained real-model
preflight in #2849 using only its saved response bytes. It must never invoke a
model, IPC broker, task runtime, or GUI.

- `PRE-REGISTRATION.md` freezes scope and gates.
- `classify_saved_stream.py` is the corrected bounded parser.
- `audit_replay.py` independently audits its retained receipt.
- `test_classify_saved_stream.py` contains ambiguous/malformed controls.
- `RESULT.md` records the exact run and disposition.
- `evidence/replay-v1/` contains additive outputs and integrity manifest.

Set `PYTHONDONTWRITEBYTECODE=1` in every Python command. The manifest
enumerator includes all regular files except `SHA256SUMS` and refuses any
`__pycache__` or `.pyc` path.
