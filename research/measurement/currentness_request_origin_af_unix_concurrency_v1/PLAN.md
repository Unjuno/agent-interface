# CURRENTNESS-REQUEST-ORIGIN-AF_UNIX-CONCURRENCY-20260918-007

BASE: `bddb2ede50dedc36aae0571c0310c45625042796`  
PARENT: #1234 / PR #1242  
EXACT CANDIDATE GIT BLOB: `3e9fc5474de9af820b653c36e5db5d912edfc076`

## H
Hold the exact request-origin currentness barrier semantics. Transfer only execution to real AF_UNIX multi-process clients feeding one runtime-owned owner loop. Owner receipt order, not wall-clock proximity, determines whether an invalidation precedes an install/use. Stale response/use must never admit; fresh post-invalidation request must still admit.

## T
Standard-library Linux container. Four persistent client processes, one AF_UNIX runtime server, one owner thread. 20,000 balanced cases over eight frozen families. Race cases release install and invalidate from separate client processes through a common multiprocessing barrier. Independent postformal oracle replays retained owner receipts without importing candidate code. Source-first publication/readback and ownership reread before primary; primary1/reruns0.

## D
`PASS_CURRENTNESS_REQUEST_ORIGIN_AF_UNIX_CONCURRENCY_SCOPED` iff cases20000, exceptions0, candidate/oracle output+snapshot mismatch0, stale installs/admissions0 under owner order, fresh paths preserved, race order agreement100%, cross-scope mutation0, replay rebindings0, duplicate invalidation double-advance0, authority promotions0, malformed transport controls fail closed, cleanup/integrity pass, primary1/reruns0.

## C
Single-host AF_UNIX plus serialized owner only. No claim for direct thread-safe candidate access, cancellation delivery, process-crash recovery, remote transport, model/task benefit, GUI/X11, production ABI or latency improvement.

## U / stop
Scheduling jitter is allowed and measured; owner sequence is authoritative. Stop after one 20,000-case formal and independent audit.

## Pre-primary A2 correction
A1 source publication occurred with primary0. Self-audit found that the corruption-summary validator incorrectly required audit-derived fields that do not exist in the raw formal result, making clean raw input invalid before mutation. A2 changes only postformal summary-validation/corruption-control plumbing: audit-derived `candidate_oracle_mismatches` and `cross_scope_mutations` remain independent audit outputs, while raw-summary corruption controls validate only raw-result fields. Candidate, transport, families, seed, 20,000-case schedule, H/D gates, oracle semantics and formal invocation count are unchanged. Primary remains0.
