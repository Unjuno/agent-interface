# Issue #6808 S04 — photometric encoding invariance

Formal status: `NOT_RUN`; candidate=0, auditor=0, retries=0. Host construction
checks are not a scientific result. S01/S02/S03 remain unchanged.

Terminal disposition: `STOP_PRE_INVOCATION_BRANCH_BASE_MISMATCH`. Freeze captured
current main `b7750c3833cd8778f11eb47bdbe61c44b1e9bc48`, while branch HEAD was
`3274083b654bcdef1c41e5fba77e33a41bab0e47`; candidate/auditor/container/retry
counts are 0/0/0/0. The frozen allocation is preserved and not amended or run.
Its successor is S06 on the refreshed main with a new branch and output path.

This allocation tests H/T/D/C/U and gates frozen in [`PREREG.md`](PREREG.md).
Exact current-main, input/source hashes, image identity, private daemon and
commands will be retained in [`FREEZE.json`](FREEZE.json) immediately before
the single candidate invocation. Formal raw output and independent audit will
be saved additively here. `FREEZE.json` is intentionally generated only after
all input/source and current-main checks pass.

See [`CONSTRUCTION.md`](CONSTRUCTION.md) for the host 3/3 package tests and
private OrbStack cgroup/daemon evidence. Scope is limited to synthetic,
threshold-mask-preserving grayscale recoding; there is no GUI, game, live
controller, safety, latency, or task-effect claim.
