# Issue #8488 — PSI-triggered work shedding before freshness collapse (T0 A01)

## Disposition

**`NO_RESIDUAL` for this frozen trace set (the predeclared PSI-incremental hypothesis did not pass).** The deterministic method artifact is independently reconstructed (`AUDIT PASS`, 32/32 rows) and four integrity mutations are rejected, but memory-PSI shedding did **not** beat the queue/deadline baseline on the primary trace. This finite authored workload does not establish a PSI-specific advantage. No runtime or deployment recommendation follows.

## Question and frozen decision

The allocation asks whether a two-consecutive-window synthetic memory-PSI trigger, suspending optional work while preserving remaining service/evidence, prevents mandatory deadline misses better than fixed concurrency and a queue/deadline trigger. Before the formal run, `PROTOCOL.md`, `inputs.json`, `candidate.py`, `audit.py`, construction tests, and precheck were SHA-256 frozen in `FREEZE.json`. The preregistered primary pass required PSI to have strictly fewer mandatory deadline misses than **both** fixed and queue/deadline policies, zero misses itself, and pass the conservation/control/mutation gates.

## Formal result

- 8 authored traces × 4 policies = 32 trace-policy rows, 16 ticks each.
- Candidate ran once (exit 0); immutable raw JSON: [RAW_RESULT.json](RAW_RESULT.json), SHA-256 `3c96d19a8edea718c0049a334ba954245cea93e5faef444813721b45b7afb94e`.
- The separately implemented auditor ran once (exit 0) and reconstructed all 32 rows exactly: [AUDIT_RESULT.json](AUDIT_RESULT.json).
- Primary `memory_burst_primary`: fixed concurrency had 4 mandatory deadline misses; queue/deadline had 0; PSI-memory had 0; free-memory had 4. PSI entered shedding at tick 3; queue/deadline entered at tick 5. The PSI-versus-queue strict-improvement gate therefore **failed** (tie at zero), while PSI-versus-fixed and PSI-zero-miss gates passed.
- Control/conservation gates: 8/8 passed, including complete factorial, mandatory-obligation representation, evidence-ID retention, no PSI shedding for the single spike, unrelated CPU/I/O, unavailable PSI, or alternating spikes, and backlog-latch conservation. Primary comparison gates: 2/3 passed (PSI beat fixed concurrency and had zero misses; strict improvement over queue/deadline failed). Thus 10/11 aggregate checks passed; the sole failure was `psi_beats_queue_primary=false` in [GATE_RESULT.json](GATE_RESULT.json).
- Adversarial integrity mutations: 4/4 rejected (signal ordering changed, one PSI event intensity changed, policy labels swapped, and non-primary rows omitted/pooling attempted): [MUTATION_RESULT.json](MUTATION_RESULT.json).

## Interpretation and limits

This result says only that, under this exact hand-authored schedule and its discrete capacity assumptions, both the early PSI policy and the later queue policy avoided the primary deadline misses. It cannot distinguish which trigger is generally preferable; the queue trigger already catches up before any frozen mandatory deadline expires. The secondary traces are finite controls, not sampled workload evidence.

Post-run source review also found that the optional-work `deferred_ticks` field is double-incremented during a shed tick for unfinished optional jobs. The independent auditor reproduces the field but does not expose this semantic counter error. Do not use that field quantitatively; see [METRIC_QUALIFICATION.md](METRIC_QUALIFICATION.md). This does not affect the preregistered deadline-miss comparison or `NO_RESIDUAL` disposition, and neither frozen output nor source was changed or rerun.

The trace values, service sizes, two-worker capacity, pressure-to-one-worker mapping, thresholds, and deadlines were authored for this test. Synthetic PSI units are informed by the kernel interface's `some` pressure definition, but this model does not read Linux PSI or reproduce kernel scheduling ([Linux PSI documentation](https://docs.kernel.org/accounting/psi.html)). It is not empirical evidence about operating systems, containers, production agents, model freshness, or service SLOs. The immutable protocol must not be retuned to obtain a favorable comparison; a materially different workload or policy requires a separately named successor allocation.

## Execution and environment

The read-only OrbStack preflight failed while listing local images because the containerd content store returned `operation not supported` on a blob. No container was started, no prune or repair was attempted, and this allocation makes no container-isolation claim. Because the frozen test is deterministic standard-library arithmetic and touches no host pressure/PSI or external state, it ran in-process on macOS arm64 / CPython 3.14.5. Exact precheck and boundary are in [PRECHECK.json](PRECHECK.json).

Pre-freeze JSON parsing, 3 construction tests, and Python compilation passed. The frozen files and digests are in [FREEZE.json](FREEZE.json). Post-run gate scripts do not alter or rerun the formal candidate or auditor. No T1 resource/pressure experiment is authorized by this result.
