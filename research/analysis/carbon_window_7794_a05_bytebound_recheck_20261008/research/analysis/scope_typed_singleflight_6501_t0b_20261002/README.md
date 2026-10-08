# Scope-typed singleflight T0b — Issue #6501

This is a **new allocation** after T0-01's immutable `STOP_OUTPUT_SERIALIZATION`. It preserves the same candidate logic, oracle, ten fixtures, and decision gates; its only execution-path change is a separately tested output wrapper that writes bytes with one real LF and exclusive-create semantics. T0-01 remains unchanged in the [sibling predecessor package](../scope_typed_singleflight_6501_t0_20261002/) and is retained for publication.

## H / T / D / C / U

- **H:** For genuinely equivalent simultaneous read-only verification requests, scope-typed in-flight coalescing reduces verifier invocations and queue/decision latency versus independent requests without unsafe admission or false shared conclusions. Predicate-only coalescing fails planted controls.
- **T0:** Two-caller deterministic single-verifier queue; 5 simulated ms service per invocation. Compare no coalescing, unsafe predicate-only keying, and scope-typed keying in ten frozen cases: equivalent overlap; different target; generation flip before return; disjoint deadlines; one cancelled waiter; owner failure; UNKNOWN; contradictory dependencies; restart/ABA; and late arrival after completion. A source-read-only CPython 3.12.14 digest-pinned WSLc container produces one raw artifact, then a separate source-read-only container invokes the independent raw-only auditor once. Network is disabled; no GUI, model, personal data, GPU, or external action.
- **D:** `PASS_METHOD_SCOPED` only if all ten cases and denominators reconcile; scope sharing joins only identical in-flight keys; each waiter retains its own deadline/cancellation/current-generation validation; owner failure and UNKNOWN are not upgraded; unsafe predicate-only controls fail; all 12 key-field changes split requests; 4ms joins an operation ending at 5ms while 6ms starts a new read; and nine copied-output corruptions are rejected. A wrong-scope or stale shared conclusion is `FAIL_METHOD`; missing evidence/hash/runtime/audit is STOP/HOLD. Latency is simulated, not wall-clock benefit.
- **C:** Existing production serialization/cache behavior may dominate; equivalent scopes may be rare; sharing can amplify a systematic verifier failure. Synthetic queueing omits real observer contention and races.
- **U:** This T0 cannot establish runtime safety, real demand correlation, GUI freshness, product benefit, or memory isolation. T1 requires a disposable fixture and independent ownership/resource review.

## T0-01 predecessor

T0-01 invoked candidate once and auditor once; both counts are terminal (no retry). The candidate process returned 0 but its output wrapper appended literal `\n`, so the auditor rejected the malformed JSON (`Extra data`, byte 10352). It is `STOP_OUTPUT_SERIALIZATION`, not a scientific verdict. See predecessor `STOP.json`, `REPORT.md`, and exact `run01/` receipts. The raw file is not copied into this successor or altered.

## T0b result

The T0b candidate ran once and the independent auditor ran once; both exited 0, retries 0. The auditor reports `PASS_METHOD_SCOPED`, 10 cases, zero violations. See `RESULTS.md`, `run01/`, and `FREEZE.json`. The simulator reports 20 independent calls versus 14 scope-typed calls across its frozen synthetic cases; those counts and its 145 vs 115 simulated-ms latency sums are not runtime measurements. In the truly equivalent overlap case, calls fall 2→1 and summed simulated decision latency falls 15→10ms. Predicate-only coalescing produces wrong shared conclusions on target, dependency, and restart controls.

The container's requested memory option is not treated as enforcement; WSLc warned swap/cgroup limits are unsupported. T0b does not prove a real scheduler benefit or memory improvement and does not unblock the separate #6389 Docker/native migration pilot.
