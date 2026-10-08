# Parallel verifier fan-out T0 (Issue #5272)

This additive artifact is a deterministic, standard-library-only scheduling
experiment. It isolates orchestration semantics from model quality, GUI state,
and external effects. It is not evidence about wall-clock speed on real
verifiers or a production scheduler.

## H / T / D / C / U

- **H — Hypothesis:** parallel fan-out reduces decision-ready latency for
  independent selected checks while preserving typed outcomes, complete
  mandatory evidence, deadlines, compute budgets, and cancellation semantics.
- **T — Test:** nine frozen workloads, each under `SERIAL_VERIFIERS` and
  `PARALLEL_FANOUT`: independent checks, dependency chain, timeout, verifier
  `UNKNOWN`, optional deadline, mandatory deadline, budget saturation,
  decisive `FAIL` cancellation, and a contention control. The model uses
  integer logical milliseconds, fixed service costs, at most three workers,
  per-case cost-unit budgets, explicit dependencies, and deterministic event
  ordering. No model, GUI, network, external verifier, or input is used.
- **D — Decision:** the primary latency gate is at least 25% lower decision-
  ready logical time for the independent workload. Every typed decision must
  match the frozen oracle; `PASS` requires all mandatory checks to complete
  with `PASS`; deadlines/timeouts/missing mandatory work yield `UNCERTAIN`;
  resource caps must hold; a decisive mandatory `FAIL` cancels outstanding
  work. Contention control determines whether fan-out necessarily helps.
- **C — Risks:** this abstraction omits host scheduling noise, real verifier
  cost distributions, GPU/RAM contention, rate limits, remote cancellation
  latency, cleanup failure, shared hidden dependencies, and useful optional
  evidence. Logical time is not measured wall time. The result cannot be
  generalized to actual agent/task performance.
- **U — Unknowns:** whether measured real verifier distributions preserve the
  independent-workload gain; whether cancellation is prompt and cleanup-safe
  across actual process/runtime boundaries; how queueing, heterogeneous
  CPU/GPU costs, and correlated failures alter policy choice; and whether
  adaptive fan-out beats fixed fan-out without weakening evidence.

## Reproduction

From this directory, using Python 3.12+ and no third-party packages:

```powershell
python -m unittest -v test_model.py
$env:RAW_OUT = "<new, absent evidence path>/raw.json"
python simulator.py
$env:RAW_PATH = "<the exact RAW_OUT path>"
python audit.py
```

The formal invocation is one-shot. `RAW_OUT` must not already exist. Run the
raw-only audit as a separate process after a successful simulator exit. Never
rerun into the same allocation/path; preserve failures and use a separately
reviewed successor allocation if a new scientific run is justified.

`simulator.py` is the runner; `audit.py` intentionally does not import it and
recomputes the case/policy matrix, constraints, typed results, and result
digests from raw output plus frozen input. Six mutation controls exercise the
auditor's rejection boundary. `test_model.py` is construction-time validation,
not the formal invocation. The formal freeze, raw output, audit report, and
result interpretation are retained beside these sources after the one-shot
run.

## Scope and merge boundary

This T0 can establish only that a deterministic scheduling model satisfies
its declared finite contract and that one synthetic independent workload
meets its latency threshold. It does not close Issue #5272 or authorize
production fan-out. A follow-up should use same-plan real verifier stubs and
measured cost/resource distributions, preserving all typed outcomes and
mandatory evidence. Any promotion is additive and remains subject to review
and applicable checks.
