# Issue #732 Rung 2 — finite async steering contract

Allocation: `resident-reactive-async-steering-732-rung2-20260921`
Disposition: **HOLD_SOURCE_HASH_NOT_PROPAGATED**
Branch: `research/resident-reactive-async-steering-732-rung2-20260921`
Base: `e6f74d3b9fef0467327823ab97cb15f0dbe59ac4`
Frozen runner SHA-256: `4d3899db4908fb0898a9c35e4ef075a9f478834420b85ef55b5e087b602fadc7`
Frozen preregistration/source manifest: [PREREG.md](PREREG.md), [FREEZE.json](FREEZE.json)

## H / T / D

**H:** generation-bound steering with safe-point parameter updates, disjoint-resource one-shots, explicit same-resource handoff, stale-message rejection, and immediate revoke can preserve bounded resident-program semantics.

**T:** exactly one finite Cartesian enumeration: 4 phases × 3 requested-resource owners × 6 commands × 2 generation-match values × 2 safe-point values × 2 bounds values = **576** rows; plus the preregistered stateful trace.

**D:** `PASS_ASYNC_STEERING_CONTRACT_SCOPED` required all 576 oracle comparisons and traces to pass, plus embedded source identity. Oracle comparisons, 576 unique cases and the eight stateful invariants matched. However the formal result JSON says `source_sha256: UNPINNED`, so integrity gate fails and disposition is HOLD. No positive PASS is claimed.

## First formal outcome

Exactly one formal enumeration ran in memory on Windows host Python 3.11.9 with `-B`; standard library only. It wrote no local files and used no Docker, CUDA, GUI, model, network or input action. The result contains all 576 rows and is retained in [RESULT.json](RESULT.json).

The launch wrapper verified the fetched runner bytes against the frozen SHA before compiling them. Harness defect: the runner reads `FROZEN_RUNNER_SHA256` from the process environment, but the one-shot wrapper passed it as a Python global instead. The frozen source therefore fell back to `UNPINNED` in its output. The one formal allocation is spent; no rerun, edit, or relabeling.

Postformal independent oracle source [postformal_audit.js](postformal_audit.js) recomputed all outcomes without importing the runner. It confirmed 576 unique rows, complete Cartesian coverage, matching outcome counts and stateful trace invariants. It intentionally returns **FAIL/HOLD** solely because the runner hash embedded in the formal output does not match the frozen hash. Full result: [AUDIT.json](AUDIT.json). The preregistered Python auditor is retained at [audit.py](audit.py), but was not run against the full payload because its large stdin could not be delivered reliably in this host harness; no claim of its execution.

The three naive negative controls demonstrate the intended failure modes: stale-generation admission, same-resource overlap away from a safe point, and revoke delayed until a safe point.

## C / U and next step

Docker Desktop's Linux engine pipe is absent and C: has zero free bytes. This is exact finite-contract analysis; a container would not add evidence about real scheduling. The result does not prove runtime concurrency, mailbox fairness, atomic OS input release, GUI effect, real-time performance, or learned/LoRA/role-network behavior.

Preserve this allocation unchanged. If pursuing implementation-level semantics, make a separate successor with the wrapper corrected and preregister a runtime-specific test; do not repeat this allocation or treat its trace fixture as runtime evidence.
