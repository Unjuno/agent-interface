# Issue #6331 T0 frozen plan

Allocation `WAKE-FENCE-6331-T0-20261002-01`. H/T/D/C/U and semantics are frozen in `PROTOCOL.md`; exact runtime source identity and image are in `FREEZE.json`; eight scenarios and four mutations are in `fixture.json`.

Candidate executes the exact current Lease source with fake, explicitly injected monotonic readings; no wall-clock wait or real suspend occurs. Candidate outputs 24 arm/scenario rows for `current_perf_lease`, `boottime_deadline`, and `wake_fence`. The auditor independently reconstructs expected outcomes without importing candidate or Lease code, then checks exact row identity/order/fields and mutations.

Construction tests passed 4/4 before freeze. Immediately before formal invocation recheck current main equals or is an ancestor of the frozen source base, Lease hash, fixture/candidate/auditor hashes, cached image ID/platform, Docker response, clean separate output directory, and no branch/path collision. Run candidate once, and auditor once only after successful candidate completion. No retries, branch-main updates, source tuning, or candidate replay after invocation; record an exact STOP/FAIL as-is.
