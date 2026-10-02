# Local CI record

## Current-main run after formal allocation 02

Revalidated after rebasing the result commit onto main `89f4fbd399f352c19f63ef543519b53fc4ed2025` (2026-10-02). The updated `.github/workflows/analysis-index.yml` sequence passed **66 tests across 12 suites**: the 59 tests from the prior sequence plus the new #6617 suite (7 tests), including #6604's 11/11. Its first run found the #6617 and #6604 directories absent from this sparse checkout (`NO TESTS RAN`, exit 5); both exact directories were added to the local sparse paths and the exact suites then passed 7/7 and 11/11. This was checkout setup, not a test or experiment result. Current-main `research/analysis/check_index.py` passed with 463 retained result/failure directories; public navigation passed with 26 documents / 1,400 relative links; workspace index passed with 156 top-level directories. JSON validation and the refreshed package SHA256SUMS passed. `FREEZE.json` and its workflow hash remain the preserved earlier freeze; main's intervening workflow change only added the independently retained #6617 suite step, and the current workflow hash is recorded by SHA256SUMS. The historical `git diff --check` note below concerns Markdown hard-break trailing spaces in preserved `PLAN.md` and `PREREGISTRATION.md`, not the experiment source/result.

Validated on 2026-10-02 from branch `research/disturbance-timescale-6604-t0-orbstack-20261002`, fast-forwarded to current main `3246a9b6cb7a19209c4056d01472cb660390c4f4` before local checks.

- Issue #6604 construction suite: **11/11 PASS**.
- Existing Analysis Index test steps: **48 tests PASS** across ten suites, including the #6590 mutation challenge after its full sparse path was materialized; #6604 adds 11, for **59 tests PASS** total. (The existing ten-suite steps were last executed on the preceding base `7ae79a8`; current-base checks below were rerun.)
- Current-base `research/analysis/check_index.py`: **PASS**, 458 retained result/failure directories.
- Current-base `.github/check_public_navigation.py`: **PASS**, 26 documents / 1,384 relative links.
- Current-base `research/check_workspace_index.py --git-tree`: **PASS**, 156 top-level directories.
- `git diff --check`: **PASS**.
- SHA256SUMS was refreshed after this record and FREEZE base metadata were updated; full manifest verification is recorded below after refresh.

- Issue #6604 construction suite: **8/8 PASS**.
- Existing Analysis Index test steps: **48 tests PASS** across ten suites, including the #6590 mutation challenge after its full sparse path was materialized; #6604 adds 11, for **59 tests PASS** total.
- `research/analysis/check_index.py`: **PASS**, 458 retained result/failure directories.
- `.github/check_public_navigation.py`: **PASS**, 26 documents / 1,384 relative links.
- `research/check_workspace_index.py --git-tree`: **PASS**, 156 top-level directories.
- `sha256sum -c research/analysis/disturbance_timescale_6604_t0_v1/SHA256SUMS`: all listed files **PASS**.
- `git diff --check`: **PASS**.

This checkout is sparse. The initial #6590 command failed because the mutation-challenge subtree and its parent candidate/auditor sources were marked skip-worktree and absent locally. After adding `research/analysis/spatial_block_position_6590_t0_20261002` to this worktree's sparse-checkout paths, the exact workflow command passed 1/1. No #6590 files or workflow step were modified.

One local invocation of #6492 `allocation-02` was initially issued from the repository root instead of the workflow's declared working directory and failed import resolution; rerunning the exact command from `research/analysis/human_return_resumption_6492_t0_20261002` passed 1/1. This is a corrected command-location setup error, not a research result or source failure.

The host-local construction/CI checks are distinct from the completed isolated OrbStack formal T0; see `formal_02/REPORT.md` and `formal_02/RUN_RECORD.json` for that allocation's evidence.
