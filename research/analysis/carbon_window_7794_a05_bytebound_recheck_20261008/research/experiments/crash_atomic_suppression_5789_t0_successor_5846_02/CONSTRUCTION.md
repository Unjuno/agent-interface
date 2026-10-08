# Construction record — Issue #5846 allocation-02

Status: preparation for a distinct allocation. Allocation-01's terminal
pre-candidate STOP is preserved at the previous package path and PR #5896; it
is not retried or reclassified. Allocation-02 has not yet run a guest,
container, candidate, or auditor; formal counts are 0/0.

## Frozen scope

- Issue: #5846; parent idea: #5789.
- Branch: `research/crash-atomic-suppression-5846-t0-20261001-02`.
- Additive path: `research/experiments/crash_atomic_suppression_5789_t0_successor_5846_02/`.
- Preparation base: main `0707d2254b2789c0bbab97d65645772c8da76a9f`; refreeze to exact main at the allocation-02 start gate.
- Allocation ID: `crash-atomic-suppression-5846-t0-20261001-02`.
- Reserved slot: 11:50–12:30 UTC in coordination Issue #5085, after a queue collision forced two successive advances to be reconciled and the conflicting provisional interval released.
- Guest/context: `crash-atomic-5846-20261001-02` / `crash-atomic-5846-local-02`.

The frozen 15-row process-crash schedule and pass/fail/STOP limits are in
`FREEZE.md`. It covers three toy persistence policies and a separate raw-only
auditor. Scope excludes power loss, physical compaction, multi-writer
serialization, product runtime, GUI effects, and product safety.

## Preserved predecessor and allocation-01 outcomes

Issue #5795 allocation `crash-atomic-suppression-5795-t0-20261001-01` ended at
`STOP_FORMAL_ARGV_MISMATCH`, candidate/auditor 0/0. Its original Issue,
branch, manifest, and Draft PR #5831 remain unchanged.

Issue #5846 allocation-01 `crash-atomic-suppression-5846-t0-20261001-01` ended
at `STOP_MAIN_ADVANCED_AT_FORMAL_START_GATE`, candidate/auditor/container/guest
0/0/0/0. Frozen main was
`56ef267db50a8937f04d940a425b2b1819f714fb`; start-gate main was
`fc1f06474149d81989099e5220c7aa197c142c6a`. Its immutable receipt remains in
the allocation-01 package and PR #5896. This was a provenance STOP, not a
scientific result.

## Construction evidence

Allocation-01 package host checks passed 19/19 unit tests, `py_compile`,
`git diff --check`, analysis index, manifest verification, and all listed
SHA256 checks. Its reviewed launcher maps `/study` guest paths to an explicit
host source root; tests cover valid mapping and reject paths outside the mount
or a relative host root. Those checks are construction-only and do not count
as candidate/auditor rows for either allocation.

## Allocation-02 provenance hardening (2026-10-01)

Read-only registry inspection separated three identifiers for the pinned
Python image: multi-platform index digest
`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
Linux/ARM64 manifest digest
`sha256:950206c37262dd86c55659797f6ee418fee30535072f65a82ed470d985f5cda5`,
and image-config digest
`sha256:8630ab77c5adf06e1f914483db4dd70e3fa59118160daab9b0ee75e685344221`.
The host OrbStack daemon's read-only `image inspect` returned `.Id` equal to
the index digest, demonstrating that the actual guest daemon `.Id` must be
observed rather than inferred from registry metadata. Formal preflight pulls
only the pinned ref through the assigned guest context and checks `.Id`,
platform, and repo digest. `finalize_freeze.py` binds that observed ID, source
commit, and host/guest path mapping into `FREEZE.json` and regenerates
`SHA256SUMS`. These are construction gates only: no allocation-02
guest/container/candidate/auditor was started by these checks; counts remain
0/0.

The inherited host rehearsal of the 15-row matrix and independent auditor
recorded 15/15 rows historically. That is host construction evidence only,
not a result for H and not fresh allocation-02 evidence. Setup/test failures
remain documented in the predecessor Issue #5795 rather than rewritten.

Allocation-02 commands (rerun after the exact source freeze):

```sh
python3 -B -m unittest discover -s research/experiments/crash_atomic_suppression_5789_t0_successor_5846_02 -p 'test_*.py' -v
python3 -B -m py_compile research/experiments/crash_atomic_suppression_5789_t0_successor_5846_02/*.py
git diff --check
python3 research/analysis/check_index.py
```

Preparation on main `0707d2254b2789c0bbab97d65645772c8da76a9f`: 19/19 unit
tests passed, `py_compile`, `git diff --check`, and the analysis index (299
retained result/failure directories) passed. These are host construction
checks only. Allocation-02's exact source commit and manifest hashes will be
re-frozen after the start-window rebase; no formal rows are implied.

At 11:50 UTC re-read main, issues/PRs/branches/queue and active guest/container
inventory, rebase and freeze to that exact main, rerun the commands above, and
verify context endpoint, image digest/platform, source/freeze/argv/mount hashes,
unique guest/path and absent/empty output paths. Any failed/ambiguous gate is a
terminal allocation-02 STOP with candidate/auditor 0/0. If gates pass, invoke
candidate exactly once and auditor only after candidate exit 0. Stop/release
the guest by 12:30 UTC, preserve all evidence, and do not retry.
