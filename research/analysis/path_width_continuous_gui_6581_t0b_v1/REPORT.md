# Issue #6581 T0b — path-width constrained GUI fixture

Date: 2026-10-02. Allocation: `PATH-WIDTH-CONTINUOUS-GUI-6581-T0B-20261002-01`.

## Result

Disposition: **PASS_METHOD_SCOPED**. One frozen candidate run emitted six scenarios (32 trusted pointer events total); one separate, raw-only Python auditor reconstructed all six and returned zero errors. Candidate and auditor exited 0. The primary wide/narrow pair had byte-identical event arrays and the same endpoint: wide saved the effect (`VALID`), narrow did not (`INVALID`). The variable-width path was rejected, the corner-union path accepted, the endpoint-after-exit adversary reached its endpoint but remained unsaved, and unconstrained drag returned `NOT_APPLICABLE` while saving its endpoint effect. All six declared audit controls passed.

The formal result and raw evidence are in [`formal_01/`](formal_01/); exact identities and commands are recorded in [`formal_01/RUN_RECORD.md`](formal_01/RUN_RECORD.md). Preregistration and immutable allocation contract are [`PREREGISTRATION.md`](PREREGISTRATION.md) and [`FREEZE.json`](FREEZE.json). The independent audit is [`formal_01/audit.json`](formal_01/audit.json).

## Interpretation boundary

This is a controlled software-defined fixture result: its app implements the declared corridor rule, and the independent auditor verifies that rule against browser-emitted trusted pointer events. It establishes that a synthetic continuous-path GUI fixture can distinguish same-endpoint traces by corridor width and preserve an earlier path exit despite endpoint recovery. It does **not** establish that ordinary GUI applications enforce path corridors, nor that humans or agents follow continuous paths. It provides no Steering-Law fit, real application/OS input, agent or human behavior, timing, task benefit, safety, or product claim. Segment interpolation between browser events is the fixture's frozen semantics, not an observation of physical motion.

## Deviations and preserved stops

Construction-only failures remain in [`construction_01/CONSTRUCTION_LOG.md`](construction_01/CONSTRUCTION_LOG.md): BuildKit overlay restriction, rejection of vulnerable Playwright 1.55.0 before any candidate use, Chromium startup at PID limit 64, and the first writable-output permission mismatch. Construction was completed after switching to Playwright 1.55.1 and adjusting only the disposable output directory/PID allowance. The first formal auditor *container launch* used an incorrect registry prefix and failed before Python or the auditor started; the corrected pinned image was then used for the auditor's sole process execution. This launch error is retained in the formal run record and did not cause a second auditor execution.

The predecessor Issue #6581 T0 `STOP_DATA` is unmodified. This successor answers only the expressly permitted synthetic-fixture question; T1/real GUI transfer remains open.
