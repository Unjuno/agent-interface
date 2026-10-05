# #8000 T0 eligibility audit — A01

**Disposition: `HOLD_NO_ELIGIBLE_LOOKUP`.** The retained repository corpus searched at the pinned current-main snapshot did not yield a source-bound trace satisfying the issue's workload gate. No candidate experiment, CPIR fixture, or container workload was run.

## Question and eligibility rule

Issue [#8000](https://github.com/Unjuno/agent-interface/issues/8000) requires a real cross-worker lookup opportunity before any synthetic method fixture: (1) a source-bound artifact held by one worker, (2) a distinct worker with a genuine claim-dependent retrieval opportunity, and (3) an observable discovery/reacquisition outcome or cost. The issue explicitly says not to fabricate demand when this evidence is absent.

## Bounded search

The audit used the tracked `research/` subtree at `b5be19963454ce5edafc945b78b100012952dd15` (the `origin/main` snapshot used for this isolated successor). It scanned 14,169 tracked `.md`, `.json`, `.jsonl`, `.py`, `.txt`, `.yaml`, `.yml`, and `.csv` files, totaling 632,058,593 bytes. Per-file and aggregate caps were 64 MiB and 1 GiB; no files were skipped. Six phrase-pattern groups targeted cross-worker retrieval/lookup/holder/artifact relations, claim-dependent retrieval, evidence-location/locator terms, broadcast/reacquisition, and holder queries. There were zero line matches. The machine-readable scope, patterns, counts, and result are retained in [`AUDIT_SCOPE.json`](AUDIT_SCOPE.json); the reproducible read-only scanner is [`src/audit_scope.py`](src/audit_scope.py).

This search supports only a bounded corpus finding. Phrase search cannot establish absence from untracked/local/external systems, omitted formats, or terminology outside the declared patterns. Any future matching lead still needs manual verification against all three eligibility conditions. Proposals, contracts, and synthetic examples do not count as executed retrieval opportunities.

## Related retained evidence and environment boundary

The predecessor [#6125 T0 eligibility result](https://github.com/Unjuno/agent-interface/issues/6125#issuecomment-5936081606) had already recorded `HOLD_NO_ELIGIBLE_WORKLOAD` under a related bounded retained-trace search. Its retained #5817 obligation-conservation report and #5339 verifier/admission contracts do not evidence a distinct worker's actual location retrieval. The #33 session-handoff capsule describes a proposed workflow, not an executed cross-worker raw-artifact lookup. These records are corroborating classifications, not a substitute for the current scan.

Issue #8000 separately records `STOP_WSL_CONTAINER_CLI_HANG` for its documented `wslc.exe run --rm hello-world` smoke test and states that container readiness is unverified. This T0 did not retry WSLc, use another runtime, or start any container. That environment STOP remains independent of this workload-eligibility HOLD.

## Reopen condition

Reopen T0 only when a retained source-bound trace (or newly authorized, privacy-reviewed trace supplied through the project's normal evidence process) identifies all three eligibility elements above. Then freeze the operator threat view and leakage, database/entry shape, schedule, maintained protocol/library/version, cost cap, and independent auditor before allocating a one-shot candidate run. Preserve this HOLD and its scan output as predecessor evidence.
