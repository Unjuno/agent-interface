# #7440 and stacked cancellation-release evidence rescue

**Classification:** evidence-only rescue from #7440 and its open dependent PRs. No candidate implementation from the old stack is adopted by this change. Source and run artifacts are preserved under their original result paths; the predecessor PRs and branches remain available until this rescue is reviewed and integrated.

## Provenance and integration decision

- #7440 head `99b7d130742b4e884709a862bc074d15e6b42ac9`, originally based on `faee077c`, is open and conflicts with current `main` `21e55a7179adc0c41a1bfd31cc4f2c0fbb14c2ab` in the v14/v15 session and input-owner/transition paths. Current `main` contains later cancellation, release-publication, and scorer-cleanup changes. The same-name V12 owner also diverged from the independent #7429 lineage. Therefore the old implementation files are intentionally excluded.
- Open dependent PRs at inventory time: #7467 (`a33f2b2b1e894bbeb26f0ebdd130d191240014bb`), #7481 (`191d55276925f0dc0284ed3072667d14c8194613`), and Draft #7468 (`99f854d18a8154b2bbb77cae9fb15820be63b706`). Their evidence-only paths are copied into this main-based rescue without changing their PR heads.
- The original one-shot candidates are not rerun. Their raw output, freeze, limitations, predecessor failures, and source identities remain historical; this rescue does not relabel them as current-main or live-control results.

## Locally rechecked saved evidence

- #7467 key-hold package: independent saved-data auditor passes 300/300 row checks and 11/11 aggregate checks. Its 14 frozen source copies match their recorded hashes; its CRLF checksum manifest verifies after normalizing line endings. Scope is 30 fake-Xlib construction cycles only.
- #7481 admission-baseline package: saved-record v2 audit passes all 12 checks and classifies `COMPOSITION_STOP_REPRODUCED`; its normalized package checksum manifest verifies. This is a retained failure/STOP, not a fix or live result.
- #7440 C01: the seven-check frozen parent/raw audit passes. C02's archived output records the one-shot 2-test pass, but re-running its historical audit against current `main` fails source/test identity checks, as expected after later source changes. C04's saved run record says one WSLc portability test passed, while the current-main source-hash checks no longer pass. Neither is presented here as a current-source reproduction.
- To make the C02/C04 historical identity independently inspectable, the exact 11-file C04 source closure was extracted from frozen commit `5934eebb2534709a8a5d282b8d1f001e6ff9eb64` into `frozen-sources/c04-5934eebb/`; all 11 hashes match `C04/FREEZE.json`. The C02 owner hash also matches that historical commit. These are archival snapshots, not replacement source files.
- #7468: the recorded 18/20 parent-only repeat with two missing standalone receipts and 20/20 with the #7429 publication barrier are both retained. The candidate/source and environment limits remain those in its frozen report (host Python, fake Xlib; no container or live game). Its old checksum list has a self-referential `SHA256SUMS` entry; the eight non-manifest artifact entries verify, but the manifest itself does not. The original list is not rewritten.

## Current-main regression spot checks

On current `main` commit `69dd261430cb1ed875f5a76411c4a2a54777c114`, the preserved cancellation-publication regression and post-sample interleaving regression each pass once (1/1, host Python 3.12.13). Exact stdout, exit codes, test hashes, and invocation metadata are retained under [`current-main-spot-checks-69dd261/`](current-main-spot-checks-69dd261/). These deterministic fake-Xlib checks validate only the exercised construction paths; they do not replace CI or constitute a live experiment.

`research/check_workspace_index.py --git-tree` passes (159 top-level directories reachable). `git diff --check` reports only four extra blank-at-EOF warnings in frozen predecessor Python scripts/tests; those bytes are intentionally preserved because their hashes are part of the recorded evidence. No production source change is included.

## Claim boundary and next action

This package rescues reproducible records, not a production fix. It establishes no physical input release, real X11/game behavior, task effect, recovery bound, or live MAP01 result. Keep #59's live gate open. After this PR is reviewed and merged, the old stack may be closed and its remote refs pruned only after rechecking all open dependents and confirming every selected result path is present on `main`; do not delete the parent stack before that gate.
