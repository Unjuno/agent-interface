# Preparation record — Issue #6575 T0

Status: `HOLD_RESOURCE_ASSIGNMENT`; formal candidate=0, independent formal auditor=0, retries=0.

The additive T0 package was prepared on planning main `7c788b3df33928d84b327bb8b4b0ac8690de13c3`. It uses three hand-annotated synthetic PPM conditions (benign text, off-task instruction, instruction-free distractor), four presentation arms, and six invalid crop probes. The source package and raw fixture bytes are SHA-256 frozen in `FREEZE.json`. This construction only checks deterministic pixel-byte provenance and rectangle visibility; it does not show that region content is semantically legible or answerable.

Preparation checks on WSL Arch Linux / CPython 3.14:

- `python3 -m unittest -v test_t0.py`: 3/3 passed.
- Corruption controls: changed crop pixel rejected; omitted candidate row rejected.
- `python3 -m py_compile ppm.py make_fixtures.py candidate.py audit.py test_t0.py`: passed.
- All 13 frozen source SHA-256 values matched after preparation.
- Fail-closed launcher check: stopped with `No explicit #5085 assignment for this exact allocation; no container invocation started.` No output directory was created, and neither WSLc candidate nor auditor was invoked.

The formal start gate requires one explicit bounded CPU/WSLc assignment for allocation `VISUAL-PRESENTATION-INJECTION-6575-T0-20261002-01` on #5085. The assignment must identify the physical-host owner. On assignment, refresh current main and collision ownership, update/re-freeze the exact source and image identities, and invoke at most one candidate plus one separate auditor if candidate exit is zero. Preserve stdout/stderr and all first outcomes; do not retry. No GPU, model, GUI, Xvfb, network, image pull/build, or real effects are in this rung. Limits are requests only; report any cgroup/swap warning.

T0 outcome is not yet measured. It cannot answer whether observation transforms change a model's response to off-task instructions; only a later separately authorized T1 could do that.
