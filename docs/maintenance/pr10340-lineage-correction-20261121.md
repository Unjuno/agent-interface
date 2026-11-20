# PR #10340 lineage correction — 2026-11-21

## Finding

The earlier r152 checkpoint attributed PR #10340's failed local rebase to a
missing shared merge base. That conclusion was incorrect: the checkout used for
the attempt was shallow (`git rev-parse --is-shallow-repository` returned
`true`), so its local object database did not contain enough ancestry for the
merge-base calculation. GitHub's authoritative compare API reports a normal
shared lineage.

## Frozen comparison

- PR: [#10340](https://github.com/Unjuno/agent-interface/pull/10340)
- Current main at audit: `9b0d64c35367f5b3e5d3c5a2f45b2079a53ee1ac`
- PR base: `86a52662dc2bb690dd670d52ea8d97816aef2a26`
- PR head: `d52ac0552d134a3c98f44023c98091da365ace86`
- GitHub compare merge base: `86a52662dc2bb690dd670d52ea8d97816aef2a26`
- GitHub compare: PR 10 commits ahead; current main 14 commits ahead.
- GitHub changed-file lists: 12 PR paths and 300 current-main paths since the
  merge base, with zero overlapping paths.
- After the supported GitHub update, base became current main
  `9b0d64c35367f5b3e5d3c5a2f45b2079a53ee1ac` and head became
  `c47ae761ed7a8c47e6d5d6b16937b468145956cd`.
- PR was OPEN and DRAFT at the initial lineage audit. No source was changed
  before the later supported GitHub update described below.

## Next bounded action

The non-overlapping paths made a current-main update plausible. GitHub's
supported update-branch operation succeeded; the new head and CI are audited
below. The remaining local test limitation is not proof of correctness or of
a code defect. Keep the PR draft and do not infer live provider, Calc, MAP01,
or integrated-efficiency evidence from the old Edge smoke.

## Evidence boundaries

This correction resolves only the repository-lineage question. It does not
prove the prospective journal's runtime integration, trusted allocation
custody, provider accounting, matched-arm comparison, task effect, or
recovery reliability. Issue #57 stays open, and no WSLc or Docker allocation
was used.

## Post-update verification (head `c47ae761ed7a8c47e6d5d6b16937b468145956cd`)

GitHub CI completed successfully after the supported rebase: `audit`,
`native-mcp`, `replay-gate`, `research-workspace-index`, and `review` all passed.
The PR still has 12 changed paths with no overlap against main.

The archived v2 Edge result independently limits its claim to one local form
POST, one completed transition, verified release, zero model resumptions, and
cleanup. It explicitly says the model is an offline double, screenshots/full
HTTP body were not retained, and the run is not provider-backed #57, Calc, or
MAP01 evidence. The PR body likewise says `dispatch_enabled: false` and no
trusted external allocation attestor is connected.

The workflow logs show why green CI does not close the local journal gate:
`review` ran runtime CLI read-only regressions; `replay-gate` ran the Doom
MAP01 scheduler replay; `audit` ran the golden adapter audit. None of these
invoked `research/integration/test_issue57_v3_prospective_run_v1.py`.

The journal's source manifest names 23 files. At least
`research/live_control/run_integrated_efficiency_live_v1.py`,
`research/live_control/calc_g10_caller_v1.py`, and
`research/live_control/calc_g10_fresh_admission_v1.py` are absent from both
current main and the PR's 12 changed paths. Thus the journal cannot attest
those components as a fully present current-main composition. It computes
hashes after creating the new evidence root, so a missing required source
raises during construction and can leave a partial, non-dispatchable root. The
current code therefore fails closed for dispatch, but lacks a focused test
that this source-incomplete path leaves no ambiguous evidence root. Moving
source validation before root creation and testing the no-partial-root result
would improve the custody boundary; this is a robustness gate, not evidence
that dispatch occurred or that an invalid run was accepted.

A local replay of the journal suite was attempted against the rebased SHA using
Python 3.11. The incomplete shallow/sparse worktree prevented a faithful source
checkout: the PR's source-hash manifest references 23 files, several of which
were not present in the worktree. The test run reached 13 tests, with 3
allocation-boundary tests passing and 10 errors at source-file lookup. The
test run is incomplete; separately, inspection found the absent-source/partial
root path described above. The old PR-body result of 12/12 normal and `-O` was
not reproduced on the new head. Do not treat the PR as locally reverified
until the complete pinned tree is available, the partial-root behavior has a
focused regression, and both modes pass. Keep the PR draft.
