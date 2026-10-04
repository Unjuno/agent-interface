# #5375 rejection-cost boundary A01

Status: prospective one-shot CPU method experiment. Nothing in this package changes the earlier #5375 T0/T1, T0-a1 FAIL, or T0-a2 PASS.

## H / T / D / C / U

**H.** Under fixed offered demand and total per-tick capacity, charging receive/parse/reject/quarantine work exposes a case where backend-only fail-fast leaves no capacity for a mandatory safety check, while upstream optional admission plus the same breaker preserves that check without deleting obligations.

**T.** A 4-policy × 4-condition deterministic finite fixture. Policies: backend-only open breaker; upstream optional limiter + same breaker; isolated safety reservation + backend breaker; no-breaker control. Conditions: nonzero-cost rejection storm; zero-cost rejection null; bounded load; and a planted obligation-drop falsifier. Thirty ticks each. Candidate emits every tick/policy/condition, queue/obligation counts, category resource accounting and terminal authority count. An independent stdlib auditor reconstructs all totals from raw rows and applies the frozen gates. Candidate and auditor each run once; no retries.

**D.** PASS_METHOD_SCOPED only if all per-tick resource equations conserve capacity, all pending obligations are carried or completed, the nonzero-cost fixture shows backend-only safety starvation and the upstream policy serves safety every tick without dropping obligations, the zero-cost and bounded controls do not falsely claim the same benefit, and the planted drop is detected. Otherwise FAIL; malformed/missing evidence or disagreement is HOLD/STOP.

**C.** An isolated mandatory lane may protect safety equally; actual rejection/quarantine costs may be negligible; simply deferring optional work can create backlog instead of recovery. Compare exact charged total work, not dispatch count alone.

**U.** Hand-authored resource units and deterministic arrivals only; no live Agent Interface workload, empirical cost, GUI, model, resilience prevalence, latency, or product claim.

## Frozen provenance

Issue #5375 latest refinement comment 5973345660; current public main at freeze: `13bab54ea6d91978247ecc1b70e5060db752367a`. Local checkout is stale and dirty; it is used only as an additive artifact workspace, not as source truth. WSLc 3.0.1.0, local `python:3.12-slim` image, pull=never, network=none, CPU=1. Cgroup/swap support will be captured from the one-shot output; no enforcement is presumed. Before invocation `wslc container list` showed zero running containers.

Formal allocation: `CIRCUIT-REJECTION-COST-5375-A01-20261004-01`. Candidate and raw-only independent auditor are source-frozen below. No live effect, network, GUI, model, or shared runtime is used.

