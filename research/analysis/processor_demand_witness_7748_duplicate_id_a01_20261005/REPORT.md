# Issue #7748 duplicate-ID boundary A01 result

**Disposition: `STOP_AUDITOR_EXIT_MISMATCH`; no scientific PASS/FAIL assigned.** The preregistered candidate ran once and exited 0. The raw-only auditor ran once and wrote `PASS_DUPLICATE_ID_BOUNDARY_SCOPED` with three rows and zero audit errors, but the auditor process exited 1. The frozen CLI still mapped only the predecessor status `PASS_CLASS_BOUNDARY_SCOPED` to exit 0. Retries: zero. The frozen candidate, auditor, raw output, audit JSON, stdout/stderr and exit receipt are preserved without repair.

The candidate output contains two distinct-ID eligible controls and one duplicate-ID row returned as `HOLD_DUPLICATE_JOB_ID`. Construction tests before freeze passed 6/6, including a read-only predecessor canary that changes the result from `POLICY_MISS_ON_FEASIBLE_TRACE` to `FEASIBLE_NO_POLICY_MISS` when the two jobs share an ID. These facts are useful diagnostic evidence, but the formal A01 allocation is stopped by its inconsistent auditor result/exit contract and is not promoted to a method PASS.

OrbStack image inventory failed before any candidate/container launch because the shared Docker Engine could not read a containerd content blob (`operation not supported`). Per the frozen fallback, the one-shot pair ran on host CPython 3.14.5; no isolation, resource enforcement, scheduler, runtime, GUI, safety, or physical-release claim is made.

Exact source and input identities: `FREEZE.json`; first outputs and command receipts: `results/`; final artifact hashes: `SHA256SUMS`. Do not rewrite or rerun A01. Any CLI repair belongs to the separately frozen A02 package.
