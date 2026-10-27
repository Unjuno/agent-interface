# Issue #8668 T0 A04 — request-bound ACK transition protocol

## Question and scope

Does binding a control/effect receipt to the exact operation ID, attempt, and issued request prevent stale or unrequested ACKs from changing the controller's cancellation/retry classification, while preserving a valid pre-emission cancellation? A03 isolated operation-ID-and-attempt binding; A04 tests the remaining request-history link. This is an offline finite-model experiment. It dispatches no GUI, OS input, runtime action, retry, or external effect.

## Hypothesis

On the frozen event schedules, a request-bound reducer will (1) preserve the valid active-attempt pre-emission cancel/no-effect transition, (2) ignore receipts from an older operation or attempt and receipts with absent/mismatched request identity, (3) keep post-emission or contradictory receipt/effect states UNKNOWN, and (4) never admit retry from neutral release or stale ACK alone. An arrival-order/type-only comparator will misclassify at least one frozen stale/unbound case. If no such discriminator exists, report `NO_INCREMENTAL_VALUE_SCOPED`.

## Frozen plant and candidate output

Each schedule explicitly supplies the operation phase, actual effect fact, issued request ledger, ordered receipt events, neutral-release observation, and retry request. Both policies process the identical schedule. Candidate outputs are classifications/eligibility only; they never create or dispatch an action. `REQUEST_BOUND` accepts a receipt only when operation ID, attempt, request ID, request kind, and phase/effect constraints all agree with the exogenous ledger. `ARRIVAL_TYPE_ONLY` uses the latest receipt kind without binding it to the ledger.

## Decision gate

`PASS_METHOD_SCOPED` iff the independent auditor reconstructs every row and rejects all frozen mutations; request-bound output has zero false completion, zero unsafe retry, zero false cancellation, zero neutral-release abort, and zero conflict-as-success; at least one valid pre-emission cancellation remains eligible for retry; and at least five frozen stale/unbound witness schedules demonstrate that binding avoids a false state transition or unsafe retry, including prior operation, prior attempt, mismatched request, absent request, and late cancellation. Otherwise use `FAIL_METHOD` or `NO_INCREMENTAL_VALUE_SCOPED` as applicable.

## Invocation boundary

Pre-freeze construction tests are nonformal and write no result output. After allocation is recorded and freeze is committed: candidate invocation once; if exit 0, independent raw-only auditor once; retries 0. Preserve any first failure. No container, GUI, model, or network is needed for this deterministic finite schedule study. Use the host's network-deny sandbox and record environment and exact commands.

## Limits

This only checks authored finite receipt/request traces and a reducer contract. It does not observe any real backend's operation IDs, request acknowledgements, actual GUI interruption, input release, latency, application effect, task outcome, or product safety. A positive result cannot authorize real retries or cancellations.
