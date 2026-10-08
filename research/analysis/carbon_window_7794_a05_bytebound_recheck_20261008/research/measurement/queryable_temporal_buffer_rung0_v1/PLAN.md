# Queryable Temporal Observation Buffer — Rung 0

TASK: `QUERYABLE-TEMPORAL-BUFFER-RUNG0-20260918-001`
PARENT: #1028
BASE: `e690e155aa00fb72a30586513caf9bfeec9a8a7d`
BRANCH: `research/queryable-temporal-buffer-rung0-20260918-001`

Natural question: can a bounded local temporal buffer answer after-the-fact history queries deterministically, with exact scope/time provenance and explicit missingness, without ever laundering historical frames into current input authority?

## H
A bounded ring plus bounded metadata indexes can retain/query recent observations by time or event/action anchor, enforce spatial/frame/byte budgets, report retention/capture gaps explicitly, and preserve HISTORICAL versus CURRENT_AT_QUERY roles without granting authority.

## T
Standard-library disposable container only. Candidate plus independently structured replay/query oracle. Fixed adversarial controls, seeded random traces, bounded exhaustive short streams, and separate tiny-metadata-budget stress. No GUI/model/provider/network/task input/shared-runtime mutation.

## D
Construction supports Rung 0 only if candidate/oracle agree; query-time age expiry is enforced; event/action anchors and gap receipts are bounded; cross-scope retrieval/gaps are impossible; ROI/frame/byte budgets are exact; unavailable intervals are canonical; stale history never becomes current; metadata overflow becomes explicit incomplete coverage; authority remains false.

## C
A deterministic synthetic buffer can pass while real capture cadence, pixel-copy/compression cost, privacy policy, and JIT-vs-continuous latency remain unfavorable. Fixed sampling policies may already suffice. Event/action anchor truth depends on the upstream causal trace.

## U
No real screenshot capture, model query, planner-boundary reduction, token saving, application correctness, or production retention claim. Rung 1 latency and Rung 2 model-demand value remain untested.
