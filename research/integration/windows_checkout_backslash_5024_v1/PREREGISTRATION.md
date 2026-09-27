# Issue #5024 — Windows checkout portability preregistration

## Lineage and frozen base

This is a repository-portability diagnostic only. It does not alter or rerun the #4561/#4570 GPU allocation and makes no change to its scientific interpretation.

- Issue: #5024
- Allocation: `windows-checkout-backslash-5024-20260928-01`
- Branch: `research/windows-checkout-backslash-5024-20260928`
- Additive path: `research/integration/windows_checkout_backslash_5024_v1/`
- Frozen main: `30793b0fcc05bb7d27c4bc1cae2aaf588321262b`
- Target subtree tree: `0f153455c8801dbce77c1013ab5a8b9f9f29e367`
- Host: Windows `10.0.26200`; Git `2.55.0.windows.3`
- Target: 48 tracked image files in `research/analysis/gpu_grounding_template_diversity_2912_v2/results/formal01/` whose Git path component contains a literal backslash. Each original path, Git blob ID and size is pinned below.

## H / T / D / C / U

**H — hypothesis.** A clean Windows checkout of the frozen repository fails on Git paths containing a literal backslash. Replacing those 48 nonportable path components with real forward-slash directory components, while preserving each blob byte-for-byte and updating only references that encode the old path, will allow clean Windows checkout without changing retained image identities.

**T — bounded reproduction and repair.** First perform a shallow, no-checkout clone of main, verify HEAD equals the frozen SHA, then attempt an ordinary full worktree checkout with the recorded Git for Windows version and capture command, exit, stdout/stderr, and partial checkout state. Do not alter that baseline clone. In a separate clean clone of the repair branch, checkout the same frozen base plus the portability change. Scan all tracked Git paths for literal backslashes; require none among the target files. Compare original/new blob IDs and SHA-256 of bytes for all 48 images. Confirm every textual reference to the old paths is either updated or shown not to encode filesystem paths. Run affected Windows CI to verify checkout proceeds into actual tests; retain Linux/macOS checks.

**D — decisions.** `FAIL_WINDOWS_CHECKOUT_REPRODUCED` if the unmodified frozen tree fails at one or more target paths. `PASS_WINDOWS_CHECKOUT_PORTABILITY_SCOPED` only if the patched clean checkout succeeds, all 48 original image bytes are preserved exactly, their old-to-new mapping is complete and independently checked, and hosted Windows CI reaches the tests while Linux/macOS remain green. `STOP_BASE_OR_ENVIRONMENT` for a main SHA/Git/version mismatch; `STOP_MIGRATION_INTEGRITY` for any blob/hash loss, collision or unresolved path reference. No scientific inference follows a STOP.

**C — controls.** Same frozen base, Windows host, Git version and checkout configuration. The only treatment is filesystem path representation and required references. Original PNG bytes, corpus semantics, allocation reports, model/source data and numerical results remain unchanged. Baseline and patched checkouts are separate; no in-place repair of the failed baseline.

**U — limits.** One repository snapshot, one Windows/Git version, one set of 48 small retained PNGs. Does not establish compatibility with every Windows Git version/filesystem, general repository portability, or any change to GPU research findings.

## Frozen offending entries

- `results/formal01/corpus\family-01__variant-0.png` — Git blob `f29e0cee88bfcf24e8f9216228ee9a32e371282c`, 552 bytes
- `results/formal01/corpus\family-01__variant-1.png` — Git blob `081269747d1cce72dbd6bbdd9637ad4c57b4532a`, 555 bytes
- `results/formal01/corpus\family-01__variant-2.png` — Git blob `b2cdb85e25bca4a8f9f09761e39b629e5dc14645`, 563 bytes
- `results/formal01/corpus\family-01__variant-3.png` — Git blob `5f6a99525d7050f73253da283da4981bb9b828fb`, 574 bytes
- `results/formal01/corpus\family-02__variant-0.png` — Git blob `1b24a08086373699aa2b7ff022186ed202ad4c2b`, 427 bytes
- `results/formal01/corpus\family-02__variant-1.png` — Git blob `86d501288a2766090721dc507f70d40c2b879397`, 436 bytes
- `results/formal01/corpus\family-02__variant-2.png` — Git blob `e6aeede907fdd3f54102d809b70eece653f1bb5e`, 445 bytes
- `results/formal01/corpus\family-02__variant-3.png` — Git blob `889ca1642e374300e51a26314bb253d3b3edfc5d`, 456 bytes
- `results/formal01/corpus\family-03__variant-0.png` — Git blob `168be543fb66e7b1f8eb6b22df5fdcdd860675ad`, 550 bytes
- `results/formal01/corpus\family-03__variant-1.png` — Git blob `2eccda381b9dbc13728e8247b6f1e3ce47d29908`, 555 bytes
- `results/formal01/corpus\family-03__variant-2.png` — Git blob `fc32a41eb1f32b1af4b01d6a8b36c5f57cc94bac`, 563 bytes
- `results/formal01/corpus\family-03__variant-3.png` — Git blob `60a506d9d9f641c8ca496b1311b6eb68dc06a50c`, 620 bytes
- `results/formal01/corpus\family-04__variant-0.png` — Git blob `c74d73db817bdfaf5e1cb052b05799a4190e1258`, 416 bytes
- `results/formal01/corpus\family-04__variant-1.png` — Git blob `0b6364be8bf3c21e15961c31bb5dda990c0d51cb`, 441 bytes
- `results/formal01/corpus\family-04__variant-2.png` — Git blob `f7e57a3561973f53026c8ce6c1d187f544e6fc25`, 432 bytes
- `results/formal01/corpus\family-04__variant-3.png` — Git blob `045b5a0d55d224428b7a14462ff8f2ba62bd26e8`, 450 bytes
- `results/formal01/corpus\family-05__variant-0.png` — Git blob `a79f71578147de783ac08a020b16f3e0ccb2ecb0`, 560 bytes
- `results/formal01/corpus\family-05__variant-1.png` — Git blob `72037214a374b1751f5ae292c980bc1dcadfe33c`, 554 bytes
- `results/formal01/corpus\family-05__variant-2.png` — Git blob `bbdbf54fa4c976f2f8490b37d2a8707ed0442dfe`, 572 bytes
- `results/formal01/corpus\family-05__variant-3.png` — Git blob `545090e61c3914bb2ade9a5f55efa93ab521910d`, 580 bytes
- `results/formal01/corpus\family-06__variant-0.png` — Git blob `3cc0b7cb0555f8b9da7e8af24cf3cbd6fba136cd`, 433 bytes
- `results/formal01/corpus\family-06__variant-1.png` — Git blob `c8debf7c4fe989ab15819a8073e538d4b1e1f72c`, 445 bytes
- `results/formal01/corpus\family-06__variant-2.png` — Git blob `cf671a4b9a85a116831d883396a62816be68d437`, 452 bytes
- `results/formal01/corpus\family-06__variant-3.png` — Git blob `90d05afff01f7ef6d689e6d031c67a0207ffc020`, 467 bytes
- `results/formal01/corpus\family-07__variant-0.png` — Git blob `e5a7bf6311ee67ba7151fdf9b5dfbcaca5e0b285`, 568 bytes
- `results/formal01/corpus\family-07__variant-1.png` — Git blob `e2e984d256a5a17b15691b08dbe4a5d0e944730e`, 570 bytes
- `results/formal01/corpus\family-07__variant-2.png` — Git blob `103da5b536254b18840975a5f38e0151028a48de`, 577 bytes
- `results/formal01/corpus\family-07__variant-3.png` — Git blob `43799a34ed4b991b71d18c4c107e9e322e382796`, 583 bytes
- `results/formal01/corpus\family-08__variant-0.png` — Git blob `47d6462788a7b7026a07e185656566146f64849b`, 470 bytes
- `results/formal01/corpus\family-08__variant-1.png` — Git blob `336c82a35e0f507f2d8419319d426e2092aaaeb5`, 487 bytes
- `results/formal01/corpus\family-08__variant-2.png` — Git blob `3bc03f25731a2f2da4f0f87961378d7bd553eeae`, 441 bytes
- `results/formal01/corpus\family-08__variant-3.png` — Git blob `0f8414feb4b1eed2e4306a2dc551067bcab09135`, 455 bytes
- `results/formal01/corpus\family-09__variant-0.png` — Git blob `9b7a447e8b677bf4520e6b5bd1689f122c6cb51d`, 530 bytes
- `results/formal01/corpus\family-09__variant-1.png` — Git blob `abde3c73a6ce79eab61adf5fc83281f7e3c5229e`, 537 bytes
- `results/formal01/corpus\family-09__variant-2.png` — Git blob `56bc7c44560681a1e3723b5785c569b8dceac894`, 548 bytes
- `results/formal01/corpus\family-09__variant-3.png` — Git blob `09d5404b77e47265bc21718636e8bab21a476792`, 591 bytes
- `results/formal01/corpus\family-10__variant-0.png` — Git blob `5c182acd90b18f0e55e8ece66f987d54c31b084d`, 425 bytes
- `results/formal01/corpus\family-10__variant-1.png` — Git blob `d4240289db3be1dcee3fee17e1742c96b42bee0a`, 436 bytes
- `results/formal01/corpus\family-10__variant-2.png` — Git blob `d6cdc57b0edbc90f9c6bdf1b26b65a164a4bb532`, 492 bytes
- `results/formal01/corpus\family-10__variant-3.png` — Git blob `46c6189623f0339a11603aff81c39d9f95660258`, 501 bytes
- `results/formal01/corpus\family-11__variant-0.png` — Git blob `45d0579162bfd631b0629ee079668b26d3aa3336`, 558 bytes
- `results/formal01/corpus\family-11__variant-1.png` — Git blob `358f8d672f4a00d11709654e234ed28c6b9584d4`, 575 bytes
- `results/formal01/corpus\family-11__variant-2.png` — Git blob `5b632279aa73c9bd0fdee8fbe3d1d20237a0df47`, 586 bytes
- `results/formal01/corpus\family-11__variant-3.png` — Git blob `0b99344f84c8f9661232c289d2f497d2219837c9`, 594 bytes
- `results/formal01/corpus\family-12__variant-0.png` — Git blob `938a22b1a4abaf3dc766c02064496b94abd4f79e`, 411 bytes
- `results/formal01/corpus\family-12__variant-1.png` — Git blob `e92d75b0136221af3dbf0f93f8f684fc6a2d2508`, 424 bytes
- `results/formal01/corpus\family-12__variant-2.png` — Git blob `eb42e89bcd6a039f239a2ac8c79e07b2368b49aa`, 430 bytes
- `results/formal01/corpus\family-12__variant-3.png` — Git blob `6751d607f0c92016b80d481b62f962ea02145bc7`, 487 bytes
