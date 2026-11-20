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

The journal's source manifest names 23 files. A subsequent `origin/main` tree
lookup established that 22 are already present in current main; the remaining
one is the journal module added by this PR. The earlier statement that three
runtime files were absent from main was caused by the local sparse checkout and
was incorrect. The test also reads
`research/live_control/integrated_efficiency_discoveries_v1.json`, which is
present in both main and the PR but was omitted from the first temporary test
tree.

A local replay of the journal suite was first attempted in an incomplete
shallow/sparse worktree: 3 allocation-boundary tests passed and 10 errored
because pinned source files were not materialized. A second temporary tree
contained all 23 pinned sources, the test, its adapters, and the discoveries
fixture from current main. Against rebased journal/test SHA
`c47ae761ed7a8c47e6d5d6b16937b468145956cd` and current-main pinned runtime
sources at `cd4857dd3a2147d2dfa0c6109361760ba6e57518`, all 13 tests passed under
Windows Python 3.11.9 in normal mode and all 13 passed under `-O`. This is
local synthetic journal/composition evidence; it does not enable dispatch,
attest a live allocation, or establish provider/live comparison results.
PR #10340 remains draft because those broader gates remain open.

The reconstructed source tree used for both successful test invocations was
`D:\CodexData\Temp\issue57-pr10340-full-tree`. It contained 23/23 paths named
by the prospective journal's source manifest plus its test and discovery
fixture (24 files before unittest caches). The PR test SHA-256 was
`f09cf956fd51cfdd55f162b63bc46dc2b86f6bbf0ddb80eb1ab379c77d271e7e`; journal
module SHA-256 was
`b31e42f226798b35b99b1498f82ed6eedec23f61ed6dfca23dcd582d5d48bbfc`; protocol
SHA-256 was
`556c04c19d19d2f87d26fdcce9a3206560593dbe4c4ab1cbe24360e72ccae1a3`;
trace-adapter SHA-256 was
`55e5e5c6f6288202ee603b096269aa5f1072eeaebed2baafe7f34399c1fa6f65`;
durable-allocation SHA-256 was
`2309b93d8f84c76eb1ced4f2b2a78f5b267d53eb30984147491fb39672ece37f`; and
the discoveries fixture SHA-256 was
`ea67ff6815da45740c194dfbf579ae1912770c8f56bedf4f1117586e58f7f335`. The
runner used `python -m unittest ... -v` and `python -O -m unittest ... -v`.
This is retained command/source identity metadata, not a live experiment raw
packet.

Exact console logs are retained outside the checkout at the same temporary
tree: `normal.log` SHA-256
`8dae4f6eb42018b492363d445ee4455c88215e48591fc5a695deafab1ca0adf5` and
`optimized.log` SHA-256
`36d8b5e716b54f2cef5f66daf4892408887e70913a374348ddaac534aec29732`. Both
record exit 0 and `Ran 13 tests ... OK`.
