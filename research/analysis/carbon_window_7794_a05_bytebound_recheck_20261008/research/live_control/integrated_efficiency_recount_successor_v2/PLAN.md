# Integrated-efficiency evidence recount successor v2

## H / T / D / C / U

### H — falsifiable hypothesis

An additive independent recount can reproduce the published single-sequence
accounting while rejecting evidence-root substitution, stale `exact: true`
submission metadata, and duplicate raw-result IDs. The audit may return HOLD or
STOP if the frozen evidence is incomplete or inconsistent; no favorable result
is assumed.

### T — bounded host-only audit

- Input tree: current-main commit `7be3499f515636875edbe071ec127fcc88714220`.
- Input: the unchanged `integrated-efficiency-live-01` record, with every file
  consumed by this recount frozen by SHA-256 and Git blob ID before execution.
- Include all three `task-details.json` files as the independent per-task
  submission/effect record; compare the raw submitted values with its expected
  token and the append-only submission history. Never accept the precomputed
  `exact` boolean by itself.
- Inventory all raw model `result.json` paths before indexing by call ID; reject
  duplicate IDs rather than allowing dictionary overwrite.
- Run the pure-CPU tests and one exact-source recount on Windows / CPython
  3.12.10. This preparation/recount does not call a model, provider, GUI, browser,
  input backend, or network service. Docker Desktop is available, but no current
  serialized container allocation is assigned to this lane, so this allocation
  is explicitly host-only and makes no container-parity claim.

### D — decision gates

`PASS_RECOUNT_PROVENANCE_AND_ACCOUNTING_SCOPED` requires all frozen input bytes
and base-commit blob IDs to match; exactly 3 preflight reports, 14 unique raw
image result files, 18 independently matched task submissions; all token and
generation totals to reconcile; and every frozen mutation control to be
rejected. A provenance/input mismatch is `STOP_RECOUNT_PROVENANCE`; a semantic
or accounting mismatch is `FAIL_RECOUNT_AUDIT`. The old v1 result is never
rewritten. Even PASS is only a corrected recount of one old sample, not a new
sample or efficiency, latency, task-quality, or product conclusion.

### C — controls

The unmodified evidence is the positive control. Synthetic controls independently
exercise a wrong checkout, a history row whose values contradict `exact: true`,
a mismatched task-detail oracle, a duplicate result ID on a distinct path, an
extra/missing raw path, and input-byte mutation. The original v1 audit and all
historical results remain byte-for-byte unchanged.

### U — limits and stop conditions

This is a host CPU audit of one existing record. It does not replicate the
model/GUI allocation, repair the pre-registration/decision-rule mismatch, add a
second sample, establish a matched baseline beyond the recorded single sequence,
or prove general efficiency. No Docker/GPU execution is authorized or claimed.
Any failed preflight is retained as STOP; no same-allocation retry.

## Frozen command and outputs

The exact source digests, input-manifest digest, input main commit, command,
runtime, and empty output path are in `FREEZE.json`. The sole entrypoint is
`run_once.py`; it retains test and audit stdout/stderr and writes only to the
new `results/host-01/` path. Do not rerun this allocation after any terminal
outcome.

## Pre-freeze construction history

Before the one-shot allocation was frozen, the first 7-test construction
invocation exposed an over-broad helper boundary: a single-row mutation fixture
was sent through the production six-row population gate (3 failures, 1 error).
A subsequent 7-test invocation had one expected-error-string mismatch because
the task-detail oracle correctly rejected the row before the history comparison.
Both were test-fixture/expectation defects, not evidence dispositions; no frozen
input, model, GUI, Docker container, or allocation output was touched. The
helper and fixtures were separated, and the final unfrozen construction suite
passed 10/10 before this allocation freeze. These prechecks are not counted as the
formal one-shot result; all are retained here so the iteration history remains
visible.
