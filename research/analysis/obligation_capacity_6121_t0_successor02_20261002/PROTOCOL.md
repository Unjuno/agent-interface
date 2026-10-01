# Issue #6121 T0-02 protocol

## H / T / D / C / U

- **H:** On this frozen near-saturated but service-feasible synthetic task family, resource/class-aware admission lowers maximum system backlog and maximum obligation age versus ledger-only admission, while completing more verified effects than global wait. It must retain the same mandatory-release lane and report overload, missing oracle, or unknown capacity without a stability claim.
- **T:** Deterministic finite event simulation; four policies (LEDGER_ONLY, GLOBAL_WAIT, FIXED_CAP2, CLASS_AWARE); five frozen arrival/service cases; separate mandatory RELEASE lane; system-wide obligation transition trace including crash, accepted handoff, timeout, failed compensation creating a child, and verified parent terminal state. An independent implementation audits every emitted field and five deliberate output corruptions are tested.
- **D:** `PASS_METHOD_SCOPED` only when the independent audit reproduces all cases and ledger transitions, observes the near-case backlog/age and useful completion tradeoff, never suppresses tick-zero mandatory release, and never labels missing-oracle or unknown-capacity cases stable. This finite synthetic result does not establish queue stability or runtime/product benefit.
- **C:** A simple fixed cap or global wait may suffice; immediate verification removes accumulated obligations. Unobservable effects cannot be made verifiable by scheduling.
- **U:** Synthetic fixed arrivals and slots do not represent correlated, nonstationary real workloads; obligation severity, external ownership, actual service time, and real effect oracles are not modeled. Finite horizon does not prove asymptotic stability.

## Frozen semantics

The five fixture cases and all policy/resource parameters are in `fixture.json`. Mandatory release is admitted independent of policy and uses its dedicated RELEASE service lane. Read-only work is allowed except that GLOBAL_WAIT holds it while any obligation is pending. Effect admission uses either no limit, no-pending global wait, a system-wide fixed cap of two, or a per-resource cap of one. A service slot counts only when that resource's oracle is available. `max_system_backlog` is measured after each obligation creation; `backlog_area` sums post-service pending counts over ticks; `max_age` is the maximum inclusive tick age before/after that tick's service. An accepted handoff changes owner only. Timeout discharges nothing. Failed compensation adds a child obligation. Verified terminal disposition closes only the named obligation.

## Invocation boundary

The prior #6121 T0 allocation recorded in PR #6149 remains `STOP_CANDIDATE_RUNTIME_ERROR / NOT_EVALUATED`; its exact frozen source is not changed or rerun. T0-02 is a distinct source and fixture successor. The candidate runs once and the separate auditor runs once in digest-pinned, network-disabled containers. No model, GUI, live effect, or external service is involved. This is method-scoped synthetic evidence only.

