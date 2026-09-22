# #2802 retrospective X11 same-timestamp ordering STOP

Status: **STOP_CASE / HOLD_EVIDENCE_INCOMPLETE**  
Scientific PASS: **none**  
Formal invocation: **1**  
Formal reruns / replacements / threshold tuning: **0 / 0 / 0**

This additive report preserves an already-consumed conversation-local allocation for
Issue #2802. It is not retrospective preregistration and does not modify or
reinterpret #1764/#1743 evidence.

## Origin

- governing Issue: #2802
- semantic parent: #1764
- unchanged temporal monitor Git blob:
  `c4c812b3e53917fd4ce102f14b689339d580ed20`
- publication branch base: `2c76b9e41fd9757cba43dd1968ed71695d8e1fd0`
- new path only:
  `research/live_control/x11_timestamp_order_contract_retrospective_v1/**`

The experiment was executed before GitHub write capability became available in
the conversation. Full local raw/source/audit bytes therefore were **not**
published or preregistered on GitHub before execution. This report must not be
used as evidence of source-complete remote reproducibility.

## H

Same-timestamp membership, observed event sequence, and causal/application order
are distinct relations. The #1764 monitor intentionally avoids assigning false
strict ordering to equal-timestamp fragments. A backend contract requiring
"B after A" therefore needs additional ordering provenance rather than silently
interpreting an equal-timestamp label set as ordered completion.

## T

Planned formal matrix: 24 fresh private-Xvfb PropertyNotify cases with separate
publisher/watcher connections, raw source event sequence and X server timestamp
retention. The upstream #1764 monitor source was unchanged. No task input,
model/provider, host desktop, user data or shared-runtime mutation.

The locally frozen first invocation stopped at the 4th case at its fixed
per-case response deadline.

## D — retained first outcome

- complete cases: **3**
- partial cases: **1**
- unstarted cases: **20**
- full allocation audit: incomplete / not PASS
- post-stop owned-process scan: no owned process group remained
- no missing exit/result was reconstructed from process absence

A separately named prefix audit recomputed only the three complete cases. It
does not supersede the failed/incomplete full-allocation audit.

### Bounded complete-prefix observations

| observed source order | X timestamps | unordered same-time monitor | sequence-aware interpretation |
| --- | --- | --- | --- |
| A -> B | same timestamp | SATISFIED | SATISFIED |
| B -> A | increasing | not satisfied / expires | same |
| B -> A -> B | all same timestamp | SATISFIED at the A prefix because {A,B} is accumulated | PENDING at A; SATISFIED only on the later B |

The third row shows why terminal equality is insufficient: prefix semantics can
differ even when the eventual terminal result agrees.

## C

- Equal X timestamps are not proof of causal simultaneity.
- Order observed by one watcher is not automatically a global/cross-connection order.
- The formal STOP prevents estimating reliability or natural frequency.
- The result does not falsify #1764; it narrows when its unordered same-time
  semantics can be transferred to an application contract.

## U

Unresolved: the remaining 20 planned rows, the partial case terminal receipt,
dropped/duplicated events, ambiguous clock domains, timestamp wrap, independent
application-event transfer, causal completion, model/task benefit, production
runtime semantics and cross-platform behavior.

## Routing

Per `docs/ISSUE_FAILURE_CLASSIFICATION.md`, this execution stop remains under
the existing #2802 scientific question. Do not create a timeout/batching-only
successor. A future justified allocation must be prospectively frozen and must
not overwrite or pool these consumed rows.

## GitHub chronology

The first GitHub retention of this local result is the #2802 comment created on
2026-09-22 (comment id 5770599763). The local evidence bundle remains outside
the repository in this publication step; a later byte-complete evidence delivery
must explicitly identify itself as retrospective and must not rerun the formal
allocation.
