# Issue #6616 A03 run record

## Frozen pre-run state

- Allocation: `history-conditioned-reliance-6616-t0-a03-20261003`
- Base main after current-main refreeze: `5e9d5b3e8d1f5685ccd71fc1ebb50b1cb729eb69`
- Superseded pre-run freeze: SHA-256 `210942a639571c235fcc932f4f7a97d32b8f8130d6090cf2d653d62b1ea1c386` on the earlier 2d5e42c2d8b9076e3b1b5f9c26cffd722f7e52aa base; main advanced before any invocation. The refreeze is prospective; no prior candidate, auditor, container or retry count changed. The earlier freeze is preserved in Git history.
- Candidate invocations: 0; auditor invocations: 0; formal container invocations: 0; retries: 0.
- Candidate output and auditor output paths on the dedicated OrbStack VM: absent at preregistration.
- Pre-run command audit caught that a shared source bind mount would make `oracle.json` visible to the candidate despite the candidate not opening it. Before any invocation, commands were corrected to disjoint mounts (`src-candidate` excludes oracle/auditor; `src-audit` is mounted only into auditor). The initial preregistration freeze is preserved in Git history and superseded prospectively; Issue addendum records the source-visibility correction.
- The initial preregistration freeze SHA-256 `1e07b1b8f7b6037cbb2c3b314a5867e9587779eaa16a3bdf9839a221aa2f1012` is superseded before execution by the corrected mount freeze. No invocation counters changed.
- A final audit-source preflight found its independent hash verifier also reads `candidate.py`. Added that code to the auditor-only source mount (still not visible to candidate), superseding the immediately previous pre-run freeze SHA-256 `192004ca1e80cbf96434208e7758ba703dab97feb112225468c43f9e2f4c598c`. No invocation counters changed.
- Construction contract tests: 6/6 passed locally before formal freeze. This is fixture-development evidence only.
- Human responses: 0; independent reviewer signoffs: 0/not allocated.
- A01 `STOP_CONTAINER_SOURCE_MOUNT_EMPTY` and A02 `HOLD_ALLOCATION_ID_MISMATCH` remain preserved in their separate packages and are not repaired, pooled, or rerun here.

Formal candidate/auditor receipts and output hashes will be appended after the single allowed execution. A candidate or auditor failure is terminal; do not retry or replace the allocation.

## Formal execution receipts (2026-10-03 JST)

- Final executed freeze SHA-256: `391c4dbad116e8d67d87d20a98598a896d99bd6c06bad3eff1e908fe020204d8`; source/base main in container receipts: `5e9d5b3e8d1f5685ccd71fc1ebb50b1cb729eb69`.
- Container counts: candidate 1 (exit 0), independent auditor 1 (exit 0), formal containers 2, retries 0. No replacement or rerun.
- VM: `research-6680-a01-20261003`, Ubuntu 24.04 arm64; Docker Engine 29.1.3; image `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`linux/arm64`). The VM is a separate OrbStack machine/Engine; it is not claimed to be network-isolated. Both containers explicitly used `--network none`.
- Candidate container `bfd7283584db03a0ab4c3a3b35d957c17e41a1d54ba4e02f6fb0e7676c370ca7`; started `2026-10-02T20:25:53.331557571Z`, finished `2026-10-02T20:25:53.739166659Z`, exit 0, OOM false. It saw only `candidate.py`, `fixture.json`, `FREEZE.json`; its mounted source and freeze were read-only. Its exact argv/environment and Docker inspect fields are in `CONTAINER_RECEIPTS.json`. Docker stdout/stderr logs were both empty.
- Auditor container `53a4bfe6e3ff2e1cecf327bdcc853a7de8c1b5132346370ae3875ce619a60e9a`; started `2026-10-02T20:26:10.145917743Z`, finished `2026-10-02T20:26:10.485909510Z`, exit 0, OOM false. It had read-only access to audit source/oracle and candidate outputs, with a separate writable audit-output bind. It did not rerun the candidate. Its exact argv/environment and Docker inspect fields are in `CONTAINER_RECEIPTS.json`. Docker stdout/stderr logs were both empty.
- Both used UID/GID 1000, read-only rootfs, 0.25 CPU, 256 MiB memory and swap, 32 PIDs, dropped all capabilities, and `no-new-privileges`. Candidate source did not contain or mount the oracle; the auditor confirmed oracle separation.
- Candidate emitted 36 rows and two reviewer packets. Independent audit reconstructed 36/36 unique rows; equal history multiset and probe × sequence × arm coverage passed; all four frozen mutations were `REJECTED`. Raw-only independent audit disposition: `PASS_CONSTRUCTION_MECHANICS_HOLD_INDEPENDENT_REVIEWER_SIGNOFF`.
- Human responses 0; independent reviewer signoffs 0/not collected. Therefore this is not an Issue-level T0 PASS and says nothing about human reliance or behavior. Final allocation disposition: `HOLD_INDEPENDENT_REVIEWER_SIGNOFF` after construction mechanics pass.
- Retained output SHA-256: `candidate.raw.json` `2c1bbacf7ad8c58c7167c625df78aa9e250c0ba3845f0d002774b85045317198`; `reviewer_packets.json` `0ebecd37de669af958bb2ecf824f48e75730c1966f0b67a38eb9da8ebe210264`; `audit.json` `a13cb7d062301d7b8e401ead8fb9ef30a871d68bef38fe68119eb812bfae3885`. VM copies and local retained copies matched byte-for-byte.
- Local validation: A03 unit suite 6/6; Python byte-compilation; package `SHA256SUMS`; analysis index 572/572; research workspace index 156/156; strict `--git-tree`; `git diff --check`; new A03 workflow YAML parse all passed. The analysis-index workflow's remaining listed test suites passed except two geometry-feasibility tests that intentionally require its preceding CI step to restore historical `.github/workflows/analysis-index.yml` SHA `b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2`; in the unmodified current local checkout they fail that file-hash assertion. Independently verified the CI-pinned source commit `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd` hashes to the expected `b190...` value. The shared analysis-index workflow itself was left unchanged; A03 has its own focused CI workflow.
