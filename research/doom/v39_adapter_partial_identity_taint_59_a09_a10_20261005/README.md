# V39 partial adapter identity taint — A09/A10

## Scope and decisions

A09 tested whether a duplicate adapter DOWN with malformed nested `owner_id` or `actuation_id`, split under a different outer `id` or `step`, could leave the original DOWN/UP timing receipt paired. On the current-main composition of PR #7690 before this repair, all eight combinations returned a paired original receipt. A10 then tested malformed nested `key` or `intent_token` under the same outer split; the A09 repair still left paired timing in all eight combinations.

The repair tracks stable partial nested-identity signatures across complete groups. When a malformed row shares an available signature, it invalidates every implicated group. An adapter identity with no usable signature taints all adapter groups in that event stream. This chooses conservative loss of unrelated timing over exposing a pair when malformed telemetry cannot be attributed.

## H / T / D / C / U

**H.** An incomplete nested adapter fingerprint can prevent a malformed duplicate from tainting the original edge group after outer `id`/`step` changes.

**T.** Use the retained A01 synthetic DOWN/UP pair and exact AST extraction of `input_edge_receipts`. A09 varies `owner_id`/`actuation_id` across null/list; A10 varies `key`/`intent_token` across null/list. Each mutation is combined with a changed outer `id` or `step`. Compare frozen pre-repair source with repaired source; independently reconstruct each result from raw.

**D.** Pre-repair source should expose one paired timing receipt in each case. Repaired source passes only if every implicated adapter receipt is incomplete and both timing intervals are null. A false pair is FAIL_OPEN.

**C.** Incomplete identities cannot always be joined narrowly. Partial signatures may conservatively invalidate other events sharing the surviving owner/actuation/key/token components; when no component is usable, all adapter groups in that event stream are invalidated.

**U.** One retained synthetic fixture and deterministic source projector only. No live X-server state, physical release, application consumption, useful task effect, threat response, recovery benefit, or MAP01 outcome is established.

## Results

- A09: frozen baseline and pre-fix composition each exposed paired timing in 8/8 cases; repaired source exposed 0/8.
- A10: pre-A10 source exposed paired timing in 8/8 cases; repaired source exposed 0/8.
- A11: malformed outer `id`/`step` with intact nested identity exposed paired timing in the frozen baseline in 4/4 cases; candidate returned `identity_unavailable` and an incomplete, null-interval receipt in 4/4.
- Independent raw replay: 54 checks, PASS across all 16 repaired cases.
- A11 independent raw audit: 13 checks, PASS across all four malformed outer identity cases.
- The PR #7727 base-to-head integration tree passes the updated 41/41 `test_map01_v39_typed_state_feedback` suite, 54 A09/A10 raw replay checks, 13 A11 raw replay checks, 50 package-verifier checks, and `git diff --check`; see `PR_BASE_INTEGRATION.json`. Main `ea5c5cba0bf18b4a78208d0b87e2ee7c48e22310` was composed conflict-free with PR head `fea78130e85ac3010a1dc5f0ad5760e3e090d8c8`; its 41-test suite and independent 65-check/20-mutation A09/A10/A11 replay both PASS. The target projector AST is unchanged in the composition. Main later advanced to `0c4be66bcaac697f1019916e3d8ada889abd5ced`; that commit only adds PR #7695's separate research package, and controller/test paths are byte-identical to the tested composition. The shallow clone has the resulting merge tree but no commit to check out, so tests were not rerun against that tip. See `LATEST_MAIN_INTEGRATION.json` and `LATEST_MAIN_REPLAY_AUDIT.json`.
- The branch-pinned package verifier is specific to the PR branch: its frozen candidate controller/A11 source pins are expected not to match the combined main tree. The independent latest-main auditor checks the composed controller hash, candidate hash, test and fixture pins, projector AST parity, and mutation outputs. A source/test-only diff check is clean; the full main-to-head `git diff --check` reports 15,070 trailing-whitespace diagnostics across 102 files, predominantly CRLF in retained evidence from the stacked base PR. Historical raw/evidence files were not rewritten to silence those diagnostics.
- Python 3.11 byte-compilation and `git diff --check` pass.

The exact A09, A10, and A11 freezes and pre-repair source/test snapshots are retained here. The raw fixture and A08 baseline remain at their original paths under `../map01_v39_perkey_bridge_a01/` and `../v39_adapter_nested_identity_taint_59_a08_20261005/`. `run_replay.py`, `audit_replay.py`, and `audit_a11.py` reproduce the results on a checkout containing these files. `CURRENT_MAIN_INTEGRATION.json` plus its replay and suite logs record current-main composition; it predates the A11 test-only addition and must be refreshed before merge.

The pinned branch package validation is recorded in `FINAL_VALIDATION.json` and `PR_BASE_INTEGRATION.json`; `verify_package.py` additionally validates the executed composition record, the later main-tip limitation, and replay audit.

This package is based on PR #7690 head `5f7cbe25ffedc20e5a16241f661fcc06bbf714cd`. This evidence does not grant or consume a live #59 allocation.
