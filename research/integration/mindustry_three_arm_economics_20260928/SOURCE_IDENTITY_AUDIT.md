# Inherited #1679 source identity audit

Audit target: `origin/main` at
`442ef765598971806dc5d671a223af7b3a711a5f` (2026-09-28 local fetch).
The preregistration is a historical record and was not edited.

| Dependency | Frozen blob in #1679 preregistration | Current-main blob | Result |
|---|---|---|---|
| `research/live_control/integrated_efficiency_protocol_v1.py` | `e8e5ee9e3abb66cb7673ac90ec9074820a16cac9` | `e8e5ee9e3abb66cb7673ac90ec9074820a16cac9` | exact |
| `research/live_control/INTEGRATED_EFFICIENCY_PLAN_V1.md` | `ff0de7c4a0d6cc57d145d460f019f72d6967ffec` | `c0c8ff37206820881b9a86d6801fbae80e0b97d6` | changed; see below |
| `research/integration/mindustry_integrated_lifecycle_mechanics_v1/RESULT.json` | `85da96306ab544a6e2f9a340b0a2af09c4701c3c` | `85da96306ab544a6e2f9a340b0a2af09c4701c3c` | exact |
| `research/integration/mindustry_repeat_reset_contract_v1/RESULT.json` | `ae4d6143370117c2c3655e61ed62a570060d55b2` | `ae4d6143370117c2c3655e61ed62a570060d55b2` | exact |
| `research/integration/mindustry_repeat_fixture_protocol_v1/RESULT.json` | `6b6b4c759ea097fadca9768d4938ac5ecf201a94` | `6b6b4c759ea097fadca9768d4938ac5ecf201a94` | exact |

The five dependency blobs were rechecked against latest main `442ef765`; all
match the prior `3553dc1` audit. The plan Markdown's complete diff from the frozen blob to current main has two
edits: the retained pre-preregistration discovery count changes from six to
eight in prose and in a summary table. The frozen decision-rule section is
unchanged, as is the evaluator Python blob. This is documentation/provenance
drift, not a changed acceptance threshold or a new scientific result. The
historical #1679 source closure remains intact; a fresh run must still pin the
current source identities and pass the live-start/resource gates.

Method: compare each recorded Git blob ID with `git rev-parse
<current-main>:<path>`; inspect the plan-only diff with `git diff
<frozen-base> <current-main> -- <path>`. No Docker, model, game, or formal
allocation was used.
