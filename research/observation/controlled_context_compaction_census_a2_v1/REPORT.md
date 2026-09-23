# Controlled context-compaction primitive census A2 — retained result

Issue #1587, task `CONTROLLED-CONTEXT-COMPACTION-PRIMITIVE-CENSUS-A2-20260918-002`.

## Decision

**`HOLD_NO_REPOSITORY_EVIDENCED_CONTROLLED_COMPACTION_PRIMITIVE`**

The scientific question and candidate ledger are unchanged from stopped predecessor #1585; A2 repairs only source-first workflow discipline.

## Source-first execution

Construction checked ledger/source/candidate shape only and recorded `eligibility_computed=false`, `formal_invocations=0`. PLAN, ledger, construction, formal, audit, corruption source and construction output were committed and remote-read back byte-identically before formal. Ownership reread found only the A2 branch/task. Exactly one formal invocation then ran; reruns/replacements/tuning0.

## Result

Four pinned-repository candidates were evaluated against all six eligibility fields: explicit request, target/thread binding, completion observability, boundary identity, retained demonstration, and actual compaction operation.

- generic `request(method, params)`: explicit transport exists, but it is not itself a compaction operation and supplies no evidence for a target-bound compaction boundary;
- `thread/start`: demonstrated and target/completion bound, but it starts a thread rather than compacting one;
- `turn/interrupt`: demonstrated turn control, not a compaction operation and not a compaction-boundary receipt;
- spontaneous context compaction retained in recovery pair3: demonstrates that compaction occurs, but it is not explicitly requestable or boundary-identifiable for matched-arm control.

Eligible candidates: **0/4**. Generic request capability is present and spontaneous compaction evidence is present, so the result is a HOLD on the missing controlled primitive, not a claim that context compaction does not exist.

Formal ledger SHA-256: `667adaa163b29c3fd0e6f8b31d341c253b665d09b7f1a9c89ea422e683bdb1f1`. Source-frozen independent audit PASS/errors[].

## Retained corruption-harness defect

The source-frozen `corruption.py` imported `audit.py`, whose audit implementation executes at module import time rather than under a `__main__` guard. As a result, the first postformal corruption invocation exited through the audit module and wrote an audit-shaped file instead of exercising the corruption cases. This does not affect the already-consumed formal result or independent audit.

The malformed first output is retained as `CORRUPTION_HARNESS_FAILURE_V1.json`. Formal was not rerun. A separate postformal `corruption_v2.py` removes the import dependency and rejects 5/5 mutations: fabricated generic-compaction eligibility, fabricated natural-compaction controllability, result count mutation, result decision mutation, and formal-count inconsistency.

## Scope

This is a census of the pinned repository and retained journals, not a statement that the external Codex/App Server product lacks a compaction API. `CodexAppServerClient.request()` can send arbitrary method names, but guessing an undocumented method is not evidence. A matched PGWS model experiment remains blocked until a compaction/truncation boundary can be explicitly controlled or externally documented, version-pinned, and observed identically in both arms.
