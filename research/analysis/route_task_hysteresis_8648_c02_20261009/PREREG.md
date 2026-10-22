# Issue #8648 C02 — route/task-mix hysteresis model

Status: prospective allocation. The previous C01 WSLc readiness STOP and its corrected auditor are preserved unchanged. C02 is a new, single-run allocation from current main with a runtime change documented before execution.

## Question and H/T/D/C/U

**H:** In the held-out `delta=20` slice of the frozen finite response model, at least three `(beta,gamma)` settings have at least three adjacent `theta` values where low- and high-initialized coupled sweeps converge to distinct stable equilibria (`|a_low-a_high| >= 0.25`, both spectral radii `<0.99`) with period-utility difference `>=0.05`; no decoupled control has the same region.

**T:** Run the deterministic candidate once, preserve stdout as raw JSONL, then run the independent raw-only auditor once against that file. The model has 4 arms, 3 beta values, 2 gamma values, 3 delta values, 2 sweep directions, 2 initial states and 21 theta points: 288 profiles and 6,048 endpoint rows plus one metadata row. The exact transition equations, tolerances, convergence horizon and thresholds are in this file's immutable C01-derived candidate/auditor sources. No GUI, model, network calls, user data, live actions, or external effects.

**D:** Preserve first outcome. `PASS_METHOD_SCOPED` requires exact independent reconstruction, all 288 profile identities and 6,048 endpoints, fixed 100-opportunity/100-correct-effect gate, convergence accounting, and 5/5 in-memory mutation rejection. `H_PASS_SCOPED` requires the preregistered held-out coupled region and no control region; otherwise a valid audit is `NO_HYSTERESIS_SCOPED`. Any audit mismatch is `FAIL_METHOD`; runtime or custody failure is `HOLD/STOP` without retry.

**C:** One-way demand response, exogenous drift, or a single-valued route response may explain changes without reciprocal hysteresis. The authored response functions may manufacture the phenomenon.

**U:** This validates only a synthetic finite dynamical method. It estimates no real user preference, task-mix shift, welfare, GUI correctness, safety, route benefit, or deployment outcome.

## Explicit C02 delta from C01

C01 was frozen to WSLc and stopped before candidate/auditor execution because WSLc failed to initialize. C02 is independently anchored to current `main` and executes the same preregistered equations and thresholds on this macOS host's CPython 3.12 after the requested OrbStack route was probed. OrbStack successfully ran the cached Node image, but could not lease/read the cached Python image; `docker pull python:3.12-slim` failed on the same content-store error. No image/container was removed or modified. The model is deterministic, CPU-only, and has no required container API or isolation-dependent behavior. This runtime delta narrows the claim to host execution and does not reinterpret C01's STOP. No candidate or auditor had been run in C01.

## Frozen execution

- Source base: current repository `main` at `bb05e4d90febe7d69cd5d673426befdefafd199c`.
- Runtime: macOS host CPython 3.12.13 at `/run/current-system/sw/bin/python3.12`; network unused.
- Candidate: `/run/current-system/sw/bin/python3.12 candidate.py > results/formal-01/RAW.jsonl`.
- Auditor: `/run/current-system/sw/bin/python3.12 audit.py < results/formal-01/RAW.jsonl > results/formal-01/AUDIT.json`.
- Each formal command is invoked exactly once; retries are zero. Candidate raw stdout must be saved before any interpretation. stderr and exit codes are retained.
- No cleanup of existing OrbStack containers/images is authorized or performed.
