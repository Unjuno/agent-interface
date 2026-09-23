# Semantic MVCC read-set v1 — Issue #4257

Allocation: `semantic-mvcc-readset-4257-20260923-01`

## H
With a complete authored semantic read set, validating the exact dependency generations plus intent version, producer generation, observer epoch and decision deadline can salvage correct in-flight results across irrelevant global observation changes, while rejecting dependency changes, UNKNOWN, intent/producer/epoch changes, ABA restoration and late completion.

## T
Authority-neutral deterministic standard-library fixture. One semantic computation reads `target_identity` and `dialog_state`, under `intent_version`, `producer_generation`, `observer_epoch`, and a decision deadline. Ten frozen cases compare `STRICT_SNAPSHOT` (requires unchanged global observation generation) with `READ_SET_VALIDATE` (requires exact read-set generation/value bindings plus intent/producer/epoch/deadline validity). Cases cover stable baseline, two irrelevant-only global changes, target change, dialog change, dependency UNKNOWN, intent change, producer-generation change, target ABA restoration with a new dependency generation, and late completion. Read-set completeness is authored by the fixture; #4233 remains the unresolved completeness boundary.

## D
`PASS_SEMANTIC_MVCC_READSET_SCOPED` only if all 10 cases reconcile; READ_SET_VALIDATE salvages both irrelevant-change cases rejected by STRICT_SNAPSHOT; both salvaged results match the finish-state oracle; all dependency/UNKNOWN/intent/producer/epoch-or-deadline controls reject; ABA restoration rejects despite exact value restoration; false accepts=0; authority_granted=false everywhere; independent raw-only audit errors=[]; >=10 coherent mutations reject; formal invocation/reruns/replacements/tuning = 1/0/0/0. A false semantic commit is FAIL; no salvage is HOLD_NO_REUSE_WINDOW; missing provenance/raw/audit is STOP/HOLD.

## C
The read set is declared complete by construction. This does not solve hidden dependencies or model preprocessing dependencies. Integer timestamps are deterministic schedule semantics, not latency benchmarking.

## U
No GUI/model/provider/live authority/task benefit/token saving or production promotion. Validation cost versus real recomputation remains unmeasured.
