# Run record

- Base: `3dbbda05eb8d5067ee2c2969615e472a0f20f562` (current main reported at start of this work).
- Candidate source: PR #7692 head `0c3627d63072b89d1c769fd0048e93baf157f5c7`, reported in preceding GitHub inspection; not refreshed in this turn because `gh` is unauthenticated. Source bytes used are hashed in `FREEZE.json`.
- Candidate command: `python candidate.py`; exit 0; emitted `FAIL_READY_COMMAND_STARVATION_ON_SAMPLE_OVERRUN`; 3 cases; 4 synchronous sample calls in each overrun case; no command bytes consumed.
- Audit command: `python audit.py`; exit 0; `PASS_AUDIT_FAIL_REPRODUCED`, 7/7 checks.
- Unit command: `python -m unittest -v test_audit.py`; exit 0; 4 tests passed.
- Environment: host CPython (version not captured at execution); deterministic fake clock/loop/scorer/stream; no container, model, GUI, game, or live allocation.
- State: local evidence package only; no remote PR or main change created in this turn.
