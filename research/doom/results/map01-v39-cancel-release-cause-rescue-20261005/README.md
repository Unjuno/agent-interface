# #7440 and stacked cancellation-release evidence rescue

**Classification:** evidence-only rescue from #7440 and its open dependent PRs. No candidate implementation from the old stack is adopted by this change. Source and run artifacts are preserved under their original result paths; the predecessor PRs and branches remain available until this rescue is reviewed and integrated.

## Provenance and integration decision

- #7440 head `99b7d130742b4e884709a862bc074d15e6b42ac9`, originally based on `faee077c`, remains an old implementation line; current `main` `9fb2dd6782d1d1477a00d14be870487fd4c54fa2` contains later cancellation, release-publication, and scorer-cleanup changes. The same-name V12 owner also diverged from the independent #7429 lineage. This rescue merges current main into the evidence branch (merge commit `dbfa95ff3`) and preserves its current indexes; old implementation files remain intentionally excluded.
- Open dependent PRs at inventory time: #7467 (`a33f2b2b1e894bbeb26f0ebdd130d191240014bb`), #7481 (`191d55276925f0dc0284ed3072667d14c8194613`), and Draft #7468 (`99f854d18a8154b2bbb77cae9fb15820be63b706`). Their evidence-only paths are copied into this main-based rescue without changing their PR heads.
- The original one-shot candidates are not rerun. Their raw output, freeze, limitations, predecessor failures, and source identities remain historical; this rescue does not relabel them as current-main or live-control results.

## Locally rechecked saved evidence

- #7467 key-hold package: the read-only preservation verifier passes 46/46 historical manifest, source, and receipt checks; safety tests pass 2/2 and confirm the historical writers fail closed without changing frozen hashes. Its 14 frozen source copies remain byte-bound. A separate current-main comparison finds 8/11 source hashes still match and three paths have drifted; see [`CURRENT_MAIN_SOURCE_DRIFT.md`](../map01-key-hold-bounds-construction-v1/CURRENT_MAIN_SOURCE_DRIFT.md). Scope remains the original 30 fake-Xlib construction cycles only; the candidate was not rerun.
- #7481 admission-baseline package: saved-record v2 audit passes all 12 checks and classifies `COMPOSITION_STOP_REPRODUCED`; its normalized package checksum manifest verifies. This is a retained failure/STOP, not a fix or live result.
- #7440 C01: the seven-check frozen parent/raw audit passes. C02's archived output records the one-shot 2-test pass, but re-running its historical audit against current `main` fails source/test identity checks, as expected after later source changes. C04's saved run record says one WSLc portability test passed, while the current-main source-hash checks no longer pass. Neither is presented here as a current-source reproduction.
- To make the C02/C04 historical identity independently inspectable, the exact 11-file C04 source closure was extracted from frozen commit `5934eebb2534709a8a5d282b8d1f001e6ff9eb64` into `frozen-sources/c04-5934eebb/`; all 11 hashes match `C04/FREEZE.json`. The C02 owner hash also matches that historical commit. These are archival snapshots, not replacement source files.
- #7468: the recorded 18/20 parent-only repeat with two missing standalone receipts and 20/20 with the #7429 publication barrier are both retained. The candidate/source and environment limits remain those in its frozen report (host Python, fake Xlib; no container or live game). Its original checksum list has a self-referential `SHA256SUMS` entry and intentionally remains unchanged. A separate [`SHA256SUMS.RESCUE`](../map01-v39-cancel-release-cause-postsample-c05-20261004/SHA256SUMS.RESCUE) excludes that self-reference and verifies the eight non-manifest artifacts; it does not repair or replace the historical manifest.

## Historical current-main regression spot checks (main `69dd261`)

On historical `main` commit `69dd261430cb1ed875f5a76411c4a2a54777c114`, the preserved cancellation-publication regression and post-sample interleaving regression each passed once (1/1, host Python 3.12.13). Exact stdout, exit codes, test hashes, and invocation metadata are retained under [`current-main-spot-checks-69dd261/`](current-main-spot-checks-69dd261/). They are not checks against current `main` `9fb2dd6`; these deterministic fake-Xlib checks validate only the exercised historical construction paths and do not constitute a live experiment.

The refresh audit verified current-main source drift without rerunning any
candidate. The #7467 one-shot runner and all historical output writers were
archived byte-for-byte; old runnable entry points now fail closed. The
self-referential #7468 manifest remains untouched, with an additional
eight-entry rescue manifest that verifies the non-manifest artifacts.
Detailed refresh evidence and CI/review gates are recorded in
[`CURRENT_MAIN_REFRESH_AUDIT.md`](CURRENT_MAIN_REFRESH_AUDIT.md).

`research/check_workspace_index.py --git-tree` passes (159 top-level directories reachable). `git diff --check` reports only four extra blank-at-EOF warnings in frozen predecessor Python scripts/tests; those bytes are intentionally preserved because their hashes are part of the recorded evidence. No production source change is included.

## Claim boundary and next action

This package rescues reproducible records, not a production fix. It establishes no physical input release, real X11/game behavior, task effect, recovery bound, or live MAP01 result. Keep #59's live gate open. After this PR is reviewed and merged, the old stack may be closed and its remote refs pruned only after rechecking all open dependents and confirming every selected result path is present on `main`; do not delete the parent stack before that gate.
