# Inherited #1679 source identity audit

Audit target: `origin/main` at
`708dec9bcd2bfb3ef597acf7bc1c8a02bcb96b01` (2026-09-29 local fetch).
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

The five inherited dependency blobs were rechecked against latest main `708dec9b`; all
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
