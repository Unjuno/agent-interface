# #4216 partial asynchronous predicate readiness — H/T/D/C/U

H: Dependency-scoped readiness can return the same graph disposition as a global barrier while refusing stale observation generation, wrong producer generation, late required predicates, and required UNKNOWN values; unrelated slower predicates must not delay Node A.

T: Authority-neutral deterministic Python `asyncio` timing fixture. Four predicate tasks per case have nominal delays 20/45/160/220 ms. Node A depends only on fast+medium. Six scenarios: NORMAL, IRRELEVANT_FALSE, STALE_OBSERVATION, PRODUCER_RECONNECT, LATE_REQUIRED, REQUIRED_UNKNOWN. Compare GLOBAL_BARRIER and DEPENDENCY_READY. Construction uses one repetition; formal uses three repetitions = 36 cases. One formal invocation only. No OS input, model/provider call, or experiment network.

D: `PASS_PARTIAL_ASYNC_PREDICATE_READINESS_SCOPED` iff all 36 cases and 144 predicate-task completions reconcile; paired dispositions equal the frozen expected table; candidate decides before `P_slow_semantic` in every case; on NORMAL+IRRELEVANT_FALSE the median candidate/global decision-time ratio is <=0.50; stale/producer/late/UNKNOWN controls all yield their typed refusal; authority=`none`, input=false; independent raw-only auditor errors=[] and 8/8 corruption controls reject. Complete scientific mismatch=FAIL. Missing/process/source evidence=STOP/HOLD.

C: Artificial delays may overstate production latency value. Event-loop scheduling is not a model benchmark. Correctness depends on complete dependency declarations and current generation/version state. The global barrier is a reference policy, not an assertion that production currently implements it.

U: No OS input, live model, task success, token saving, cancellation-compute saving, cross-platform timing, calibrated uncertainty, runtime promotion, or product claim. Timing is descriptive local wall time only.
