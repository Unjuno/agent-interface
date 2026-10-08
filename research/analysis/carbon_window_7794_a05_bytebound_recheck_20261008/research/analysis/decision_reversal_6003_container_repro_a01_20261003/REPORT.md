# Issue #6740 — OrbStack container reproducibility A01

**Status:** candidate executed once and failed before producing a selector result.
**Disposition:** `FAIL_RUNNER_IMPORT_COLLISION_NO_METHOD_RESULT`. The independent trace classifier passed its narrow failure-chain check; the predeclared mathematical auditor was not run because no candidate result existed.
**Allocation:** `6003-container-repro-a01-20261003`.
**Frozen base:** `94112d59c76f9bcccb3c80582e43a750348ad520`.

This is an additive successor to #6003 and Draft PR #6042. It leaves the original host-only result and its artifacts unchanged and asks only whether that frozen finite selector reproduces under an actual, isolated OrbStack container boundary.

## H / T / D / C / U

- **H:** The frozen #6003 selector and independent checker, run in isolated OrbStack containers on arm64, reproduce the predecessor's selector choices and audit invariants exactly; otherwise retain a scoped runtime divergence or STOP.
- **T:** Run one candidate and then one independent audit in separate digest-pinned local Python containers, network disabled, read-only root/input, 1 CPU, 256 MiB, 64 PID limit, dropped capabilities, no-new-privileges, temporary output on tmpfs. No model, GUI, GPU, package install, image pull/build, shared-container access, retries, or tuning. Exact source/runtime commands are in [RUNBOOK.md](RUNBOOK.md).
- **D:** Pass only if both invocations exit 0, audit errors are empty, cheapest and nominal entropy select A, robust reversal selects B, prior-rank reversal holds, null is UNRANKABLE, the mandatory sentinel remains, STOP contributes no support, and these values match the predecessor. A failed runtime gate is STOP; divergence or audit defect is retained as FAIL/HOLD.
- **C:** One synthetic finite table, one OrbStack Engine 29.4.0 arm64 host, one locally present pinned Python image, one candidate and one auditor invocation.
- **U:** Reproducibility of an authored method only. No calibrated-prior, real roadmap utility, research-productivity, GUI/runtime, safety-effectiveness, or broad portability claim follows.

The predecessor candidate and audit hashes, outputs, and source lineage are retained in [RUNBOOK.md](RUNBOOK.md). Only output scope/status labels differ in the two scripts; [SOURCE_DIFF.md](SOURCE_DIFF.md) and the construction test verify those are the sole source changes.

Before candidate launch, preservation-only merge #6210 advanced main from the first observed `89c67103de1e3061ff070c62825dac12041c5333` to `94112d59c76f9bcccb3c80582e43a750348ad520`. The branch was fast-forwarded and the base amended before any candidate/auditor execution; the predecessor fixture is unchanged.

## Pre-run local construction

The non-executing construction tests validate the frozen input hash, finite fixture, syntax, and metadata-only source deltas. They do not invoke candidate or auditor code.

## Executed outcome

The candidate container was launched once with the frozen command. It exited `1` before reaching `OUT.write_text(...)`: the script is named `select.py`, and while `platform.platform()` inspected the processor, Python's `subprocess` import loaded `selectors`, which resolved the local `select.py` instead of the standard-library `select` extension. The retained traceback ends with `AttributeError: module 'select' has no attribute 'select'`.

- Candidate: 1 invocation, exit 1; selector ranking not evaluated; candidate result not emitted.
- Predeclared mathematical auditor: 0 invocations; gated because there was no candidate result to audit.
- Post-hoc independent trace classifier: 1 invocation in its own network-disabled, read-only OrbStack container; exit 0, `errors=[]`, classification `FAIL_RUNNER_IMPORT_COLLISION_NO_RESULT`. Its stdout is retained in `execution/failure_trace_audit.stdout.log`; the report was written only to ephemeral tmpfs and could not be copied after container exit. No auditor rerun was attempted.
- Candidate stdout SHA-256: `ef8181e6dc1f006e27ea5bb59f10ba451832d16386363c5176c57398161e8679`.
- Trace-classifier stdout SHA-256: `ab36a3369de932e374e99d4b39aa933d730cca43006acc896c3c68cb3bc60dc7`.
- Exact image/runtime/limits, container IDs, and output-retention caveat are in `execution/CANDIDATE_FAILURE.json`.

This failure is a runner/import-boundary defect, not a scientific result for cheapest-first, entropy, or decision-reversal selection. No candidate retry or source tuning occurred in allocation A01. A distinct successor is required to evaluate the frozen method with a namespace-safe launcher.
