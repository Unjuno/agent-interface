# Issue #4733 — allocation STOP: source/freeze mismatch

## H / T / D / C / U

- **H:** As frozen in `FREEZE.json`, a cost/selectivity ordering derived from
  development false probabilities preserves exact AND semantics and can be
  compared across a finite held-out drift grid.
- **T:** One Docker Desktop/Linux amd64 invocation, allocation
  `predicate-order-drift-4258-20260927-01`, against current-main intake
  `21f81b3e6e41491bca9078a4d5adfd577c041f64`. The image was the already-cached
  `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
  Network was disabled, the source mount and container root filesystem were
  read-only, and only `/out` was writable. The executed producer and first
  auditor are preserved byte-for-byte as run.
- **D:** `STOP_SOURCE_IMAGE_OR_AUDIT`. The first audit incorrectly returned
  PASS because producer and auditor both interpreted the frozen
  `development_false_probability` as true probability. A separate forensic
  posthoc audit (`audit_result_posthoc_v2.py`) reads the freeze and raw result
  without importing either first-run program; it reports 604 freeze/result
  discrepancies. In particular, the specified cost/false-probability order is
  `C,B,A,D`, while the executed record says `A,B,C,D`; the frozen source-state
  probability is `243/2500`, while the raw record says `2/625`. The grid costs,
  distributions, and claimed no-crossover classification therefore do not
  answer the frozen hypothesis.
- **C:** The disagreement is an implementation/specification interpretation
  error, not evidence about real predicate costs or runtime behavior. The
  first auditor shared the same mistaken probability convention as the
  producer, so its nominally independent recomputation was not independent of
  that assumption.
- **U:** No drift-boundary finding, optimizer benefit, real latency, online
  adaptation, GUI, or runtime claim is supported. The allocation is consumed;
  no retry or corrected rerun was made. The initial raw result and initial
  audit remain preserved, including their incorrect `PASS` label, with the
  posthoc contradiction recorded additively.

## Retained execution record

- `FREEZE.json`: intake and decision rules.
- `run_experiment.py`, `audit_result.py`: exact sources mounted read-only for
  the one invocation; not repaired after execution.
- `results/docker-formal01/raw.json`, `audit.json`: original container outputs.
- `audit_result_posthoc_v2.py`,
  `results/docker-formal01/audit_posthoc_v2.json`: independent forensic
  comparison against the frozen probability semantics. This is not a rerun.

The only supported conclusion is that the attempt failed its source/freeze
conformance gate. Any scientifically useful corrected study would need a new,
separately coordinated successor allocation; it must not reuse this allocation
or rewrite this record.
