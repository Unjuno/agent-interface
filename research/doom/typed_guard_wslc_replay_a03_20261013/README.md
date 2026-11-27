# WSLc typed-policy replay portability A03 — 2026-10-13

This additive package preserves allocation `WSLC-TYPED-POLICY-REPLAY-A03-20261013-01`, its original A01/A02 STOP records, raw launcher bytes, candidate and independent audit outputs. The original package is bound by `PACKAGE_MANIFEST.json` and `SHA256SUMS.txt` (28 files; manifest SHA-256 `dcfab20aa8cefc310c2dae43e8cf063b80ac53f82153b5c133ab161a9780c1a8`; checksum-file SHA-256 `692c28e2d1fe7c3dd8c99ddf526eb503fce923846d1e9c2a86e9c21e182cb1dc`). The retained report SHA-256 is `4bc7238e6b15723f9cac201024044f1f05f0c8f6ced0c96bed4e73de3275e1a7`.

## H/T/D/C/U

- **H:** A direct typed-signal adapter using the exact current-main `ObservableSignalGuard` can reproduce selected retained V39 health/ammo policy outcomes in the pinned Python image on WSLc; an independently written raw-only auditor can reconstruct those outcomes without artifact extraction or input authority.
- **T:** One WSLc invocation from source `964c9197d5083ab55ea7fdc9105427623e89e677`, guard Git blob `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`, pinned image `python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd`, with network disabled, one CPU, requested 512M, read-only input, dedicated output, and bounded host/stage deadlines. Candidate and independent auditor each ran once.
- **D:** `PASS_PORTABILITY_SCOPED`: both exited 0; four selected rows match; ammo sequences 96 and 160 are `SOFT_CHANGED`; health sequences 99 and 170 are `UNKNOWN/source_expired`; authority is false on every row; scoped query for the exact container ID found no remaining container.
- **C:** This is a small construction harness around the production pure guard. The auditor independently derives outcomes from raw source values and does not import candidate or guard code. A01 host-output decoding STOP and A02 absent-image STOP are retained unchanged. A03 uses a fresh allocation ID and changes only capture handling, evidence-backed image digest, and host bind path.
- **U:** No production-controller integration, game, model, GUI, OS input, task effect, live invalidation delivery, recovery, survival, or task success was tested. The retained report selects two soft-event rows while reporting a cumulative total of three, so the replay does not reconstruct every counted soft event. WSLc warned that swap-limit support was unavailable; requested 512M does not establish effective memory enforcement. No Docker comparison, cost, or memory claim follows.

## Result and reproduction

Candidate and audit hashes are preserved in the package manifest. The output records the CID `6a70d0de613ee39e06d105d732f9b4fd04a8384f105cffd4c1a4a7fff25e9fa7`; no container remains. See [REPORT.md](REPORT.md), `freeze.json`, raw `output/`, and `prior_stops/` for the invocation, source identities, outcomes, and original failures. Do not rerun allocation A03. The report documents saved-data verification commands; those commands are not another WSLc run and make no additional runtime claim.

This is evidence preservation for Issue #59, not its gated live threat-exposure allocation or its exit condition. The live lane remains unassigned; do not infer live control, threat response, recovery, or MAP01 progress from this construction result.
