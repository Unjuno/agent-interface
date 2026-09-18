# #24 status-before-retry synthetic rung

Decision: **PASS_STATUS_BEFORE_RETRY_SCOPED**

## Question

When an ordinary completion receipt is missing at a recovery timeout, should the interface immediately replay the semantic operation, or first query an authoritative read-only operation ledger?

This rung holds identity checks and operation semantics fixed. It changes only the recovery decision after the missing receipt:

- `RETRY_ON_TIMEOUT`: immediately submit a fresh attempt.
- `QUERY_THEN_DECIDE`: query status first. COMPLETED/RUNNING/EFFECT_UNKNOWN do not replay; FAILED_BEFORE_INPUT/NOT_FOUND remain retry-eligible.

The primary effect is deliberately non-idempotent: one counter increment is the only permitted semantic effect.

## Formal result

Frozen seed `240120260918001`; one invocation; 160,000 traces / 320,000 paired arm rows; reruns/replacements/tuning 0.

- candidate duplicate non-idempotent effects: **0**
- blind-retry comparator duplicate effects: **70,072**
- candidate/oracle mismatch: **0**
- candidate unsafe replays after COMPLETED/RUNNING/EFFECT_UNKNOWN: **0**
- eligible retry preserved for FAILED_BEFORE_INPUT/NOT_FOUND: **40,000 / 40,000**
- altered-parameter/cross-session negative-control new effects: **0**
- status-query task effects: **0**
- authority promotions: **0**
- false COMPLETED claims: **0**
- outcome digest: `a1cddf7ee9e81499a16c9c5a3753acd18447afcaeedb85f2ba749d0191ad0f5a`

The 70,072 comparator duplicates consist of all completed-lost, completed-delayed and running cases plus the hidden-effect-positive subset of EFFECT_UNKNOWN. The candidate does not inspect that hidden truth; it returns typed uncertainty without replay.

Independent audit regenerates the full corpus and passes with errors[]. Four copied-result corruptions are all rejected.

## Interpretation

A read-only authoritative status query can separate “receipt missing” from “operation safe to replay” in this synthetic contract. Blind timeout replay is unsafe for non-idempotent operations once input may already have started or completed. Status-first preserves the two cases where the frozen ledger proves no input effect (`FAILED_BEFORE_INPUT`, `NOT_FOUND`) while refusing to convert `EFFECT_UNKNOWN` into false certainty.

This does not finish #24. It establishes only the recovery-decision rung. A real implementation still needs durable status provenance, bounded retention/expiry, operation-specific idempotency policy, and live GUI/task evidence.

## Limits

Pure standard-library state-machine evidence. No GUI/X11, model/provider, real durable journal, planner-boundary/token savings, network loss process, or live task correctness. The status ledger is assumed authoritative in this rung; loss/corruption of that ledger remains open.
