# Prospective one-shot protocol — Issue #6358

Allocation: `ADOPTION-CONDITIONED-RECOURSE-6358-T0-MAC-HOST-20261003-02`
Frozen main: `fc1c09294458d3b2744fa05432d4cf8a19583f18`
Prior outcomes: preserve #6358 allocation-01 `STOP_RUNNER_REDIRECTION_DIRECTORY_MISSING` and local Mac A01 `STOP_RUNNER_OUTPUT_PARENT_MISSING`; neither candidate process started.

## H / T / D / C / U

- **H:** In the frozen synthetic shared-capacity fixture, individually feasible advice can become collectively infeasible under synchronized adoption; predeclared recipient-specific authorized routing can preserve verified cohort outcomes without suppressing valid work or weakening safety. This should not help under disjoint resources or ample capacity.
- **T:** One local CPU-only candidate invocation over the immutable eight-case/seven-policy fixture, followed—only on candidate exit 0—by one independent raw-only auditor invocation. This fresh allocation changes only the allocation ID, output path and runner staging. The previous two allocations stopped before a candidate process began; neither is replayed.
- **D:** `PASS_METHOD_SCOPED` only if candidate, independent audit, corruption controls and frozen primary/control comparisons all pass. Otherwise retain exact FAIL/HOLD/STOP. Synthetic output is not causal or deployment evidence.
- **C:** Cases and method unchanged from preregistered v2. One candidate, one conditional auditor, no retries, tuning, network, model, GUI, GPU, container, production service or actual retry/actuation.
- **U:** One Mac host, CPython 3.14.5, deterministic synthetic scheduler. No claim about real multi-agent/human adoption, prevalence, production capacity, or end-to-end task benefit.

## Preflight and invocation

1. Confirm GitHub `main` is still the frozen SHA and source hashes match `FREEZE.json`.
2. Run construction unit tests and `git diff --check` before the formal allocation.
3. Confirm `results/formal-02/` exists in the committed package and candidate/audit/stdout/stderr files are absent.
4. Invoke the candidate directly once; no `mkdir` or redirection wrapper is part of its launch. Preserve returned stdout/stderr/exit plus the raw file. Run the independent auditor once only if candidate exits 0.
5. Any failure after candidate start is terminal for this allocation; no retry or repair.

```sh
python3 -B candidate.py --cases cases.json --out results/formal-02/candidate.raw.json
python3 -B auditor.py --cases cases.json --candidate results/formal-02/candidate.raw.json --out results/formal-02/audit.raw.json
```

The second command is conditional on candidate exit 0. `results/formal-02/` is pre-created and committed; no directory-creation command is run at formal time.
