# Result: recomputed-row integrity control for the #4766 raw auditor

Issue: [#4932](https://github.com/Unjuno/agent-interface/issues/4932), successor to closed [#4766](https://github.com/Unjuno/agent-interface/issues/4766) and merged [PR #4779](https://github.com/Unjuno/agent-interface/pull/4779). Trigger: unresolved P1 review comment 4114411753.

## Disposition

**PASS_AUDIT_CONTROL_REPAIR_SCOPED.** The historical false pass was reproduced twice on the unchanged 64-row trace. The additive auditor rejects every recomputed-row mutation across all 45 `MISS`/`RECOMPUTE` rows, while the intentionally stale `STATIC_DECLARED` hit remains an accepted negative-control observation. The unmodified evidence still yields `PASS_DYNAMIC_READSET_SCOPED`; the corrected auditor rejects 10/10 corruption controls. Four regression tests and the separate raw-only value/identity audit pass.

This is a post-hoc auditor-integrity correction, not a rerun, replacement, or revision of #4766's consumed formal allocation. The historical report, auditor, trace, and raw log remain untouched.

## H — hypothesis

The raw-only auditor must compare every row reporting a recomputation (`MISS` or `RECOMPUTE`) against a value independently derived from its frozen state. It must not impose that equality on cache hits, because the deliberately incomplete `STATIC_DECLARED` policy is retained as a stale-hit negative control.

## T — diagnostic and verification

Inputs are the original main-branch files under `research/analysis/predicate_readset_runtime_proxy_4233_v1/`:

- `audit.py`: Git blob `d54458636c17c5d7b83cb57f11007b42bc35b21c`; SHA-256 `2f332c7a1f415d1990e76d00143ff15edf17ee9f4440e2afcaba767099041083`.
- `trace.json`: Git blob `200b2a05a275f62819342ceaddaadc05097ee82c`; SHA-256 `5a60df268a80551f860d2b7859356f677ea01278b27d41ed2ef82036ddb8bc97`.
- `raw.jsonl`: Git blob `898a8bb2b7ee7e84d546b2a39c76e237dd1b324d`; SHA-256 `af9dace34a667a2e75c002c0848286801237de52e2c27b3f698fabb5010b565f`.

Two targeted mutations first established the defect: `STATIC_ALL/s4/TARGET_MATCH/MISS` changed from `true` to `CORRUPTED`, and `STATIC_DECLARED/s0/READY_TO_SUBMIT/MISS` changed from `ALLOW` to `CORRUPTED`. In both cases the historical auditor returned `PASS_DYNAMIC_READSET_SCOPED`, `errors=[]`, and `mutation_controls_rejected=8`.

The new auditor generalizes the oracle check to every `MISS`/`RECOMPUTE` row and adds those two mutations to its built-in corruption controls. The unittest suite explicitly reproduces the historical false passes, exhaustively corrupts each recomputed row, checks that all such corruptions are rejected, and preserves the stale static-declared hit.

Commands, run with Python 3.12.10 from the additive directory:

```text
python -m unittest -v test_audit.py
python -B audit.py ../predicate_readset_runtime_proxy_4233_v1/trace.json ../predicate_readset_runtime_proxy_4233_v1/raw.jsonl audit.json
python -B verify_evidence.py
python -m py_compile audit.py test_audit.py verify_evidence.py
```

Observed: 4/4 unit tests pass; audit reconciles 64 rows with errors `[]` and 10/10 mutation controls rejected; independent check derives the oracle from the trace and checks all 45 recomputed rows, preserving one stale static-declared hit.

Successor artifact SHA-256 values (exact files tested):

- `audit.py`: `898d2c9bfb5af0ec05ac11a61efc9456b808b405cbbe1b71c502ff7dda322c3a`
- `test_audit.py`: `6a0c58e24c4a2f8ec8b57f226fc63ed89d4f1ac321b78e9b000528e6848ea814`
- `verify_evidence.py`: `62db172b37235afa173da49f48277210633b321c78adb80624ed0c4a31a76bd0`
- `audit.json`: `319a21ab56ad2b5078401c8cb536cafd8503f5607a16e5161f284d22abd1ac21`
- `independent_audit.json`: `39168f984a778363a23e0ae2fe17649cb390226c68390ece9e2ad8d65396e9e6`

## D — decision gates

`PASS_AUDIT_CONTROL_REPAIR_SCOPED` requires: both historical counterexamples reproduce; all recomputed-row mutations are rejected; the untouched baseline remains 64/64 and retains the prior metrics; ten auditor corruption controls reject; the one expected stale static-declared hit remains; input identities verify; and unit plus independent checks pass. All gates passed for this diagnostic.

## C — controls and preservation

- Identical frozen trace/raw inputs for historical and corrected auditors.
- Original eight corruption controls retained; two static recomputation-value controls added.
- The one expected stale `STATIC_DECLARED` hit is not reclassified as an error.
- No edits to #4766's historical artifacts and no calls to the formal runner, model, or GUI.

## U — limits and stop record

This is one deterministic post-hoc audit check on a small synthetic trace. It does not broaden the underlying dynamic-readset result to arbitrary Python, concurrency, latency, production runtime, or user tasks. It does not invalidate the original study's scoped mechanism observation; it shows that the old auditor's 8/8 mutation suite did not cover all policies.

Docker Desktop and backend processes were present, but `docker info` and `docker version` produced no Engine response during bounded waits and were interrupted. Preserve `STOP_DOCKER_ENGINE_UNRESPONSIVE`. Tests therefore ran on the Windows host, not in a container. No repository clone was made (the reported repository size exceeded currently free C: space); exact source and data came from GitHub MCP.

The applicable repository analysis index is updated in the PR. CI remains the integration gate; no merge or product/runtime promotion is implied before it passes.
