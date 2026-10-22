# PR #8838 evidence custody review (2026-10-19)

PR [#8838](https://github.com/Unjuno/agent-interface/pull/8838), exact head `810fdcfe558ad700f779aaa66c111a4cc19eb9e4`, contains two distinct evidence packages and no production-source changes. Its parent Issue #8681 is closed and its sole implementation path, #8771, is merged. Preserve the packages before closing this draft; do not treat its historical results as current-main or live-control proof.

## What the packages establish

- **A06 finite construction:** enumerates 245,411 ordered sequences of length 0–4 over a fixed 22-event alphabet. The candidate frozen from #8687 matched the independent oracle on all represented inputs; the frozen main source had 92,690 false-positive verified-empty certifications and 1,118 order-sensitive multiset profiles. This is bounded parser/receipt semantics, not a production frequency or external-effect result.
- **A07 focused regression:** the frozen candidate passed five tests in normal and optimized CPython 3.12.3; the frozen main source failed three assertions across two duplicate-identity tests in each mode. Its independent audit corrected the runner's whitespace/subtest counting while retaining the original runner output.
- A07's `DEVIATION.md` is material: WSLc stopped before test execution because the D: bind-mounted runner path was unavailable. The tests then ran in native Ubuntu WSL with `cpu.max=max 100000` and `memory.max=max`; no CPU or memory confinement is claimed. The attempted fallback, harness errors, and raw outputs remain part of the immutable record.

The frozen “main” source is commit `f185a9059d485a4f8d5a65e9e7f6782897f67eae`, and the candidate is #8687 commit `6195600931fa6de4ecf1a5012cb83b549addb5af`. These are historical snapshots, not the current merged #8771 implementation. The evidence does not test event production, physical input release, GUI/game effects, useful feedback, bounded recovery, or end-to-end control. No candidate, auditor, runner, or allocation was rerun for this custody review.

## Preservation verification

The two package directories were copied from the exact #8838 head without line-ending conversion. Offline checks verified all 30 entries in the package SHA-256 manifests and all 32 Git blobs against the original head. The manifest files themselves are included but, as usual, do not hash themselves. No package file was edited.

After this evidence-only destination is merged and read back from main, #8838 can be closed as superseded because its complete diff consists of these two preserved packages and its parent Issue's code path is already represented by #8771. Close the PR only after that readback; consider remote-branch removal separately after checking branch use and registered worktrees.
