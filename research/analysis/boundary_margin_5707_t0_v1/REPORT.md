# Issue #5709 / #5707 T0 first outcome

**Disposition: `FAIL_METHOD_HYPOTHESIS_NOT_IDENTIFIABLE`.** The frozen six-row fixture and its row-level raw audit behaved as expected, but the experiment does not compare two policies under the same opportunities. `comfortable` and `thin` are two scenario labels with different authored margin vectors; within each row, `policy_a` and `policy_b` are identical. Therefore the result demonstrates that a ledger can display two different synthetic margin levels, but does not test the preregistered H about distinguishing policies. Do not promote this to `PASS_METHOD_SCOPED`.

## Frozen question and method

Issue #5707 proposed an advisory boundary-margin ledger. Successor #5709 froze six deterministic cases and the decision rule before execution on 2026-10-01. Publication base was `ac361bfe1d2e7fd615f0a6102b166e4c08cd7a07`; branch `research/5707-boundary-margin-t0-20261001`; image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.

The source pins are in `MANIFEST.json`. No source or threshold was changed after the single formal runner invocation. The first container setup attempt used an incorrect, unstarted mount; that container was inspected and removed before any code ran. The actual preflight and formal runs used the dedicated sparse checkout and the pinned image, with networking disabled.

## Executed checks and first outcome

Preflight command:

```text
docker run --rm --name ai-5709-preflight-20261001 --network none -v "$PWD":/src:ro -w /src/research/analysis/boundary_margin_5707_t0_v1 python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B -m unittest -v test_audit.py
```

Result: 4/4 passed, including baseline plus missing-time, opportunity-identity and crossing-sign corruption controls.

One formal invocation, exit 0:

```text
docker run --rm --name ai-5709-t0-formal-20261001 --network none --read-only --tmpfs /tmp -v "$PWD":/src:ro -v "$PWD/out":/out:rw python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/research/analysis/boundary_margin_5707_t0_v1/runner.py /out/raw.jsonl
```

The separate raw-only auditor ran in a second read-only, network-disabled container and returned `{"disposition":"PASS_METHOD_SCOPED","errors":[],"rows":6}` for the frozen row-level checks. Raw output SHA-256: `1db88de351360423d20b93053980102ae7d679a3477b819cad4fc9b172c4dd4d`.

The records show: comfortable margins `[100,90,80,70]` ms and thin margins `[12,11,10,9]` ms, each with zero crossings and forbidden effects; crossing `-3` ms correctly marked; safe stop retained as `STOP_RECORDED_OUTCOME_UNKNOWN`; missing time marked `UNKNOWN`; and changed opportunity count marked `HOLD_NO_STABLE_DENOMINATOR`. These are synthetic scenario outcomes only. In particular, the row-level audit PASS does not repair the design mismatch between scenario levels and policy comparison.

## Scope / next research step

This outcome is a method/design failure, not evidence against real-world safety margins or the value of the idea. No live system, clock, task, GUI, model, or physical effect was involved. It establishes no harm probability, predictive validity, near-miss prevalence, or safety improvement.

The allocation is consumed; do not rerun or retrofit it. A fresh successor must define two actual policy arms receiving identical exogenous opportunity IDs and an independently frozen external event/effect stream, with only the policy-derived boundary slack changing. Preserve this first outcome unchanged.