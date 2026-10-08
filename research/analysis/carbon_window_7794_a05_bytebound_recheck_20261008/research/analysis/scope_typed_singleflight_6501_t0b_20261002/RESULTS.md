# T0b-01 result — Issue #6501

**Disposition: `PASS_METHOD_SCOPED`.** Formal candidate=1, independent auditor=1, retries=0. The candidate and audit artifact are valid JSON with a single actual LF terminator (last byte 10); source, fixture, and result hashes are retained.

## Formal result

- The candidate emitted ten frozen cases and three mechanisms. The independent raw-only auditor independently replayed every case, all caller outcomes, invocation counts, completion receipts, and simulated latency values: 10/10 audited, zero violations.
- Across the synthetic suite, verifier invocations were 20 without coalescing, 11 for unsafe predicate-only keying, and 14 for scope-typed coalescing. Summed per-caller **simulated** queue latency was 145ms, 100ms, and 115ms respectively. These are outputs of the frozen 5ms serial-service model, not measured CPU/wall-clock performance.
- For the single truly equivalent overlap case, no-coalescing uses two calls and simulated decision latencies 5+10=15ms; both predicate-only and scope-typed use one call and 5+5=10ms. Scope-typed shares only that identical pending scope in this fixture.
- Predicate-only keying fails deliberately: the non-owner receives `WRONG_SHARED_TRUE` in the different-target and contradictory-dependency controls, and a wrong shared conclusion in the restart/ABA control. Scope-typed output keeps each request's own correct result.
- Generation change returns `STALE_ON_RETURN` to both waiters; the early-deadline waiter misses its deadline while the later waiter succeeds; cancellation remains waiter-local; owner failure remains `OWNER_FAILED`; UNKNOWN remains UNKNOWN; and a late post-completion request starts a new call.
- Construction controls on the pinned WSLc image passed 24/24, including 12/12 scope-key field mutations, the 4ms/6ms pending-return boundary, and nine copied-output corruption rejections. T0-01's separate output STOP remains immutable.

## Reproduction / limits

Formal commands and image identity are pinned in `FREEZE.json`. Each formal command used WSLc 3.0.1.0, cached `python@sha256:f77ac9e...`, CPython 3.12.14, network disabled, source read-only, output-only mount, and requested 0.25 CPU. Candidate wall time was 1,269ms and auditor wall time 1,301ms including container invocation/overhead; these are not the simulated decision-latency metric. WSLc emitted the unsupported swap/cgroup limit warning. No memory-enforcement claim is made.

This is a deterministic synthetic method result only. It does not show actual runtime serialization, demand correlation, GUI freshness, application-effect correctness, an end-to-end benefit, or permission to share action authority. It is unrelated to and does not alter #6389's native-vs-WSLc HOLD. No Docker Desktop daemon or unknown-owner pre-existing WSLc container was used or modified.
