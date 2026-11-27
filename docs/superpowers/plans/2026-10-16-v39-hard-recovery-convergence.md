# V39 saved hard-recovery convergence plan

**Goal:** Preserve PR8792 and its corrected final-admission audit, establish saved evidence applicability without rerunning its producer or treating historical scoped replay as current live control.

**Source:** PR8792 `e27c0b43625bbe986b8363c448e52abdb20ebc10`; original controller commit `743ae74ec5be2472ff27fa06fe13d5ecf8534de5`; base main `8908da5ed28af1273bddbaf9ebe710dcf5307152`.

**Architecture:** Preserve all original bytes as inert images with original-path mapping, avoiding discovery of old tests that assume frozen runtime sources. Isolate saved-only audit execution in a new output directory with exact frozen source bytes as data. Retain audit unit checks and deliberately false final-admission controls, then compare source hashes with current main. No old actor/producer runs; no production changes.

**Constraints:** Inert saved-data inspection/local audit Python only; no GUI/native/model/provider/WSL/container/allocation. Historical verified-release fixture is not physical release. Current-source mismatch cannot be rewritten into historical PASS.

- [x] Preserve original package, checksum results and source identity.
- [x] Audit all saved records against frozen source: latest passes, older normal/optimized records fail fresh-source checks. Corrected authority tests normal/-O pass; retain current-source rejection and mutations.
- [ ] Publish source applicability/remaining live gates, review immutable patch, integrate and verify; close only converged PR8792 preserving original refs.
