# Barrier-aware coalescing for noncritical progress events

Decision: **PASS_BARRIER_AWARE_PROGRESS_COALESCING_SCOPED**.

Task: `EVENT-PROGRESS-COALESCE-20260917-001`
Publication BASE: `421b2d1053f94ca12635d1747766ee54451dd1c8`
Issue: #712

## Question

Can repeated equivalent noncritical progress records be summarized without letting a summary span a causally meaningful critical event?

This rung changes only coalescing semantics. Critical-event retention/classification, ACK/backpressure/capacity, retries, priority scheduling, batching and input authority are out of scope.

## Container-first method

Construction before freeze:
- `py_compile`: PASS
- unit tests: **9/9 PASS**
- formal runner invocations before freeze: **0**

After exact SHA-256 source freeze:
- formal runner: **1 invocation**
- formal reruns: **0**
- deterministic verifier: **PASS_VERIFY**
- post-result source hash recheck: **7/7 exact**

## First formal result

All **8/8** frozen gates passed.

| Case | Reference | Naive global coalesce | Barrier-aware candidate |
|---|---:|---:|---:|
| progress storm | 100 records | 1 summary | **1 summary** |
| critical barrier | 11 records | **1 progress summary spanning TARGET_LOST** | **2 progress summaries + exact TARGET_LOST** |
| critical pair | 4 records | critical records retained | **TARGET_LOST then LEASE_EXPIRED independently retained** |
| non-equivalent targets | 5 records | global-by-key aggregation | **A(2), B(2), A(1) contiguous summaries** |
| cross-session | mixed A/B stream | key-scoped summaries | **session-scoped summaries; A critical event unchanged** |

Frozen aggregate:
- authored critical records: **4**
- candidate retained critical records: **4**
- naive summaries spanning a critical seq: **1**
- candidate summaries spanning a critical seq: **0**
- progress storm: **100 -> 1** planner-visible records

The 12-record confidence summary retained exact bounded sufficient statistics:
- `first_seq=1` / `last_seq=12` / `count=12`
- `worst_confidence=0.67`
- `latest_evidence_id=conf-ev-12`

## Interpretation

The negative control demonstrates that grouping equivalent progress over an entire buffered interval can retain the critical event itself while still producing a progress summary whose declared sequence interval crosses that event. The candidate avoids this ambiguity by treating every critical record and non-equivalent progress key as a causal barrier.

This is narrower than planner batching or interrupt scheduling. It supports only the rule:

> coalesce replaceable/repetitive progress within a contiguous equivalence run; never summarize across a critical causal transition.

## Boundary

This deterministic fixture does not establish actual model-token savings, planner-boundary savings, real watcher rates, delivery latency, classification correctness, production queue sizing or task success. A live/model comparison is justified only if the integrated feedback path adopts this representation.
