# Issue #5694 finite opportunity-clock T0

Disposition: **PASS_METHOD_SCOPED (synthetic only)**. This validates the narrow ledger method against a constructed ranking inversion; it is not live-control evidence.

## H / T / D / C / U

**H.** When independent opportunities continue during declared planner-busy intervals, completed-cycle p95 can look better for a sparse controller even as its useful-opportunity coverage falls; an all-opportunity ledger should expose that inversion without inventing timing when clocks are unsynchronized.

**T.** On 2026-10-01 UTC, ran one finite deterministic standard-library simulator with a frozen 12-opportunity schedule at 100 ms cadence and 90 ms expiry. Seven scenarios cover no stall, true useful-fast control, sparse fast cycles with two declared busy intervals, safe stop, expiry, overlapping opportunity IDs/windows, and unsynchronized clock domains. The candidate emits all outcomes in one JSON raw. A separately implemented raw-only auditor ran once after candidate exit 0. Six unit/mutation tests ran before the candidate. No model, GUI, game, input, Docker container, network, or live GitHub workflow was involved.

**D.** `PASS_METHOD_SCOPED`. The true useful-fast controller completed 12/12 opportunities (coverage 1.0, completed-cycle p95 35 ms). The sparse/busy controller completed 5/12 (coverage 0.4167) yet had a lower completed-cycle p95 of 10 ms. The independently enumerating auditor returned `errors=[]`, retained the 12-row denominator, validated all seven scenario summaries, and detected the inversion. Safe-stop was kept distinct from useful effect; two overlapping opportunities remained two denominator entries; unsynchronized timestamps remained null/UNKNOWN. Six tests passed, including rejection of denominator deletion and fabricated unsynchronized timestamps.

**C.** The schedule, expiry, controller latency, and busy intervals are hand-constructed deterministic values. This is a method demonstration, not a model of empirical cue distributions or controller behavior. The overlap case verifies denominator cardinality only; it does not model resource contention or causal assignment between simultaneous effects. The synthetic outcome oracle is perfect by construction.

**U.** This establishes no live opportunity coverage, survival, task-effect quality, safety, human-tempo, or general agent-performance claim. Transfer requires a task-defined exogenous opportunity source, independent scorer, aligned clocks (or explicit UNKNOWN), all-attempt traces, and a separately authorized fixture. Histogram correction or counterfactual actions are not justified.

## Execution record

- Repository state read before work: main `6872f2f028dde8a20cd27d71416b2a8d04f0b8cf` (latest commit visible through GitHub MCP at start); open Issue #5694.
- Candidate command: `python -B scratch/issue5694_t0_20261001_01/opportunity_ledger.py --out scratch/issue5694_t0_20261001_01/raw-candidate.json` — exit 0, exactly once.
- Auditor command: `python -B scratch/issue5694_t0_20261001_01/audit_opportunity_ledger.py scratch/issue5694_t0_20261001_01/raw-candidate.json` — exit 0, exactly once. Output retained in `audit-result.json`.
- Construction tests: `python -B -m unittest discover -s scratch/issue5694_t0_20261001_01 -p 'test_*.py' -v` — 6/6 passed before candidate execution.
- Python: CPython 3.12.10, Windows host. Only Python standard library. No dependency installation.
- Raw SHA-256: `8bbdfd86095e7eb6f1804ecdf9e29f5ad9231f94fa80837d2b6df6508fa28792`.
- Candidate source SHA-256: `d290bb2b95e9890a94a2c8b8a5d400297ac9f0585cc1a4fafdcb8117baff2281`.
- Auditor source SHA-256: `abdc6d66b9b9436438e0a1dd61f8aa06b9f83ada63073cc22f935049bd3a9b94`.
- Test source SHA-256: `6a9c43332511f4a64452bce3d458a6c5c7329d57cc62ea2667c2ea03019d358d`.

## Protocol note

The issue's H/T/D gates and finite-simulator scope preceded this work, and the candidate was not edited between the pre-candidate six-test run and its single execution. However, the source SHA-256 values were captured after candidate/audit execution, not in a separately retained pre-execution freeze record. This limits provenance strength; the hashes identify the retained bytes but are not contemporaneous freeze receipts. Docker Desktop's `desktop-linux` context exists, but its read-only daemon API check timed out after 10 seconds; the issue explicitly makes this first T0 a local standard-library simulator and forbids claiming a Docker/live allocation. No Docker action was attempted beyond that read-only check.

