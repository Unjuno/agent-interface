# Preparation record — Issue #6575 T0

Status: `SUPERSEDED_NO_RUN`; this package's formal candidate=0, independent formal auditor=0, retries=0.

The additive T0 package was prepared on planning main `7c788b3df33928d84b327bb8b4b0ac8690de13c3`. It uses three hand-annotated synthetic PPM conditions (benign text, off-task instruction, instruction-free distractor), four presentation arms, and six invalid crop probes. The source package and raw fixture bytes are SHA-256 frozen in `FREEZE.json`. This construction only checks deterministic pixel-byte provenance and rectangle visibility; it does not show that region content is semantically legible or answerable.

Preparation checks on WSL Arch Linux / CPython 3.14:

- `python3 -m unittest -v test_t0.py`: 3/3 passed.
- Corruption controls: changed crop pixel rejected; omitted candidate row rejected.
- `python3 -m py_compile ppm.py make_fixtures.py candidate.py audit.py test_t0.py`: passed.
- All 13 frozen source SHA-256 values matched after preparation.
- Fail-closed launcher check: stopped with `No explicit #5085 assignment for this exact allocation; no container invocation started.` No output directory was created, and neither WSLc candidate nor auditor was invoked.

Before an assignment arrived, current main merged PR #6582 for the same #6575 T0 hypothesis. That consumed allocation `OBS-INJECTION-TRANSFORM-6575-T0-20261002-01` stopped as `STOP_HARNESS_FIXTURE_MISMATCH` after six sham-crop provenance errors; no model was called. I withdrew my unassigned #5085 request (#5946629393) and recorded the collision on #6575 (#5946630607). This duplicate package has not run and must not be launched as a repair/retry of the consumed question.

T0 outcome is not yet measured. It cannot answer whether observation transforms change a model's response to off-task instructions; only a later separately authorized T1 could do that.
