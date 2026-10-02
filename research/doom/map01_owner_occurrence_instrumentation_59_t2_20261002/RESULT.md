# Result — per-occurrence owner instrumentation construction

**Disposition: `PASS_INSTRUMENTATION_CONSTRUCTION_SCOPED`.** On the frozen,
isolated copy of the pinned #5630 `InputOwner`, two repeated `W down/up`
occurrences each received a distinct ID. Each ID binds its admission, explicit
release bracket, and three full 32-byte fake-XQueryKeymap witnesses
(`pre_down`, `post_down`, `post_up`). The independent raw-only auditor passed
all nine checks. Candidate and auditor each ran once with exit code 0; retries:
0.

Raw SHA-256:
`eaed03bc5dd3bc27ba7c255993fbba11e6af2204e2e3f67dca60ec80e2ea85e1`.
Audit SHA-256 is listed in `RESULT_HASHES.json` after capture.

## Interpretation

This demonstrates that the proposed record linkage and witness fields can be
constructed in this isolated prototype while preserving repeated event order.
It does **not** show that XQueryKeymap witnesses prove physical key state,
input authority, held-input duration, target-application receipt, useful
feedback, bounded recovery, or improved MAP01 control. The witnesses explicitly
grant no input authority and make no physical-key-up claim. T0 and T1 artifacts
remain untouched; this is their additive successor, not a replacement.

The TDD construction history is preserved in `CONSTRUCTION.json`, including
the red failures and a detected interval-ID mismatch caught before the final
construction pass. Frozen inputs are identified in `FREEZE.json` and
`SOURCE_HASHES.json`; candidate/auditor sources were not changed after freeze.

## Scope and environment

WSL Ubuntu, Python 3.12.3; CPU-only in-process fake Xlib. No Docker container
was used because no shared container slot was allocated and the Docker Desktop
engine was unavailable. No real X server, GUI, game, model, physical input,
application effect, physical key state, occupancy duration, latency, or safety
outcome was measured. A follow-up requiring native X11 or game evidence needs a
separately allocated environment and successor allocation.
