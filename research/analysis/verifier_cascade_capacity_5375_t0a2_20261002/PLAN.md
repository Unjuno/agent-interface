# Issue #5375 T0-a2 — capacity-conserving post-trigger cascade

## H / T / D / C / U

- **H:** In a finite synthetic trace where a temporary verifier outage leaves retry debt, a legacy shared-pool retry-feedback policy can sustain low safety-service after the fault is removed; retry-debt shedding plus one explicit safety reservation can return to service without granting fallback authority.
- **T:** Three policies × three 30-tick cases: underload/no-trigger; finite outage and debt with feedback disabled; same finite outage/debt with bounded feedback of three retry units per tick while debt exists. Four total service units/tick include ordinary service, safety service, and failed-attempt resource. Policy arms are legacy shared retry, retry-debt shedding + one safety unit reserved, and shared-pool no-retry control. Retain every tick as JSONL.
- **D:** `METHOD_PASS` requires all 270 rows to satisfy primary/retry/safety queue conservation, queue bounds, chronology, zero authority admission, and the joint resource invariant `primary_service + retry_service + safety_service + failed_attempt_resource <= 4`. The no-trigger and feedback-off arms must recover by the final eight ticks. `HYPOTHESIS_SUPPORTED_MODEL_SCOPED` requires the feedback-on legacy arm to provide zero safety service and retain positive retry debt for each final eight ticks, while debt-shed/reserved and no-retry controls provide safety service on each final eight ticks. Otherwise `HYPOTHESIS_NOT_SUPPORTED_IN_FROZEN_GRID`, or HOLD on any method violation.
- **C:** Bounded arrivals and retry feedback can make all policies stable; debt shedding may discard useful work; reserved service may lower ordinary throughput. These are explicit controls/limits, not tuned away after freeze.
- **U:** Synthetic deterministic queues only; no real verifier, concurrency, runtime, workload, calibration, latency, GUI/task safety, or product claim. A result does not establish real metastability.

## Prior failure and successor boundary

This is a new allocation after #5375 T0-a1's `FAIL_METHOD_CAPACITY_CONSERVATION`; its source, raw rows, audit, and disposition remain untouched. T0-a2 explicitly counts failed-attempt resource and both service classes against one shared capacity, and caps feedback generation at three units per tick. The independent auditor checks the joint capacity invariant on every row before interpreting any policy contrast.

## Resource / execution

- Allocation: `CIRCUIT-METASTABILITY-5375-T0-A2-20261002-01`.
- Base: current main `a39606e9ea31d9eb56aa1a4591f7577a4e195656`.
- The repo-wide OrbStack queue (#5085) currently prohibits another container while `unjuno-native-ci-6092` remains running. Therefore this allocation uses bounded, standard-library host CPython CPU only, as the immediately preceding #5375 plan explicitly allowed when Docker was unavailable. No Docker command launches/stops/inspects the other container. No network, model, GPU, GUI, input, or user data.
- Construction tests precede freeze. Candidate and independently implemented raw-only auditor each run exactly once after freeze; zero retries. Any method-gate failure is retained without repair/retry.
