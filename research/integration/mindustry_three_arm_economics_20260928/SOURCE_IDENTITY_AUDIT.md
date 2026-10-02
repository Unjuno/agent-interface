# Inherited #1679 source identity audit

Audit target: `origin/main` at
`f7c7dd8caf2db49add9b85bb68a3660dcb48af70` (2026-09-29 local fetch).
The preregistration is a historical record and was not edited.

| Dependency | Frozen blob in #1679 preregistration | Current-main blob | Result |
|---|---|---|---|
| `research/live_control/integrated_efficiency_protocol_v1.py` | `e8e5ee9e3abb66cb7673ac90ec9074820a16cac9` | `1adbd176d3290530dd4b01280f9b6892fb542bd1` | changed; PR #5176 adds matched model/effort checks |
| `research/live_control/INTEGRATED_EFFICIENCY_PLAN_V1.md` | `ff0de7c4a0d6cc57d145d460f019f72d6967ffec` | `c0c8ff37206820881b9a86d6801fbae80e0b97d6` | changed; see below |
| `research/integration/mindustry_integrated_lifecycle_mechanics_v1/RESULT.json` | `85da96306ab544a6e2f9a340b0a2af09c4701c3c` | `85da96306ab544a6e2f9a340b0a2af09c4701c3c` | exact |
| `research/integration/mindustry_repeat_reset_contract_v1/RESULT.json` | `ae4d6143370117c2c3655e61ed62a570060d55b2` | `ae4d6143370117c2c3655e61ed62a570060d55b2` | exact |
| `research/integration/mindustry_repeat_fixture_protocol_v1/RESULT.json` | `6b6b4c759ea097fadca9768d4938ac5ecf201a94` | `6b6b4c759ea097fadca9768d4938ac5ecf201a94` | exact |
| `research/live_control/mindustry_receipt_session_v1.py` | not in #1679 freeze | `2386c3d425f00ed23da802033c21e4048d417e96` | reused for #55 post-model target revalidation |
| `research/live_control/receipt_target_admission_v1.py` | not in #1679 freeze | `a6b50ba3767b88e04654790fb343cd234cfd4bda` | reused for #55 receipt checks |
| `research/benchmark_discovery/mindustry_single_tile_interactive_v1.py` | not in #1679 freeze | `40c473b2ec7b1b06d403bd814abe15cb2e07a6cc` | frozen child source delegated to additive backend adapter |

The five inherited dependency blobs were rechecked against latest main `f7c7dd8c`; all
match the prior audit, with the evaluator adding
cross-preflight and preflight-to-task model/effort identity checks in merged PR
#5176; the plan Markdown's complete diff from the frozen blob to current main has two
edits: the retained pre-preregistration discovery count changes from six to
eight in prose and in a summary table. The frozen decision thresholds are
unchanged. The evaluator equality invariant is stricter for malformed or
incomparable traces; it does not alter the valid matched-trace score gates.
This is an additive protocol correction, not a new scientific result. The
historical #1679 source closure remains intact; a fresh run must still pin the
current source identities and pass the live-start/resource gates.

Method: compare each recorded Git blob ID with `git rev-parse
<current-main>:<path>`; inspect the plan-only diff with `git diff
<frozen-base> <current-main> -- <path>`. No Docker, model, game, or formal
allocation was used.

The three Issue #55 receipt-revalidation dependencies above are byte-identical
to the recorded `origin/main` blobs. They are additional current-main runtime
dependencies, not additions to or modifications of the historical #1679
freeze.

## Lifecycle-complete raw auditor v2 — host construction (2026-09-29)

V1 did not reconstruct reset witnesses or the A3→B1 geometry change from raw
rows. V2 adds exact per-task pre/reset 112-tile snapshots and timestamp ordering
(independent score < reset request < reset witness < next task), plus one
same-surface, changed-geometry event between the A3 reset and B1 start for each
arm. The reset projection checker is separately implemented; v2 does not import
the candidate reset auditor, runner, or controller. V1 raw/audit bytes remain
unchanged and are retained as the earlier, partial-schema result.

The synthetic fixture is `construction/raw_audit_v2_20260929_01/` with raw
SHA-256 `58e61347f45538ecc6d6f732ae41529d4b28152c09d166de039da4ac761f450c`.
Its output is `PASS_CONSTRUCTION_ONLY`, evaluator disposition `RETAIN`,
break-even task 2, 18 reset witnesses, and three geometry transitions. Source,
model, game, and image identity fields remain sentinels; this is not a live
result. The v2 corruption suite passes 12/12; the entire integration package
passes 84/84 locally. Adversarial huge tick, deep nesting, and non-standard
NaN cases return fail-closed HOLD rather than escaping the audit. Initial implementation failures were caught by those
tests and repaired before the final pass; they were auditor/test-fixture
defects, not experiment outcomes. No Docker, GitHub Actions, model call, game
process, or formal allocation was used.
