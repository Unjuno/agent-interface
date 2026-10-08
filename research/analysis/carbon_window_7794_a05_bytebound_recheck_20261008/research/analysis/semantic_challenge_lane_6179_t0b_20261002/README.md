# Isolated verifier challenge lane — Issue #6461 / successor to #6179

This directory holds one finite synthetic experiment allocation. The parent #6179 T0 result remains unchanged; this successor addresses only its missing executable broker-boundary controls.

- `PREREGISTRATION.md` — frozen H/T/D/C/U and scope.
- `candidate.py` — authored finite lane and envelope submissions.
- `auditor.py` — separate raw-only reconstruction; imports no candidate code.
- `test_protocol.py` — construction and auditor mutation tests.
- `RUN_PROTOCOL.md` — exact one-shot WSLc gates and evidence handling.

No production verifier, live application, model, GPU, user data, or external side effect is in scope. A PASS can support only the finite synthetic protocol-method claim stated in the preregistration.

## Current state

Construction is not frozen yet. Host-only development tests passed, but they are not formal experiment evidence. No candidate or auditor allocation has run in WSLc. Do not interpret this README as a result; the post-gate raw bundle and independent audit determine disposition.
