# Issue #4985 — O3 source-window composition boundary

This additive successor tests one narrow composition seam related to #4782 and #2692. It does not alter either issue's previous allocations, live results, or runtime code.

## Reproduce

Read [PLAN.md](PLAN.md) and [formal/RUN.json](formal/RUN.json) for frozen H/T/D/C/U, source/image identities, exact one-shot local Docker argv, outcome, raw-output hashes, and invocation receipt.

Run from a disposable local checkout with the pinned cached Docker image. The experiment is CPU-only, network-disabled, read-only except for a fresh output mount. The candidate calls only pure helpers; Xlib imports are stubbed and live access raises. No GitHub workflow executed the experiment.

## Result

See [RESULTS.md](RESULTS.md) and [formal/raw.json](formal/raw.json). The independent auditor is frozen at [src/audit.py](src/audit.py); its formal output and mutation controls are retained under [formal/](formal/).

Scope is limited to synthetic current-main composition behavior. No caller contract, live X11 behavior, bypass, or product/security claim follows.
