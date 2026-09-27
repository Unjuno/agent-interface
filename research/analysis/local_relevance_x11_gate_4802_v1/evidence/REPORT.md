# Issue #4802 formal result — HOLD_MODEL_NO_SAFE_UTILITY

## Outcome

The frozen model made **zero false suppressions** on 24 held-out task-relevant/critical pairs, and correctly sent all 8 critical cases through the unconditional critical override. But it suppressed **0/16** held-out clear-irrelevant pairs: every irrelevant probability was below the frozen `0.98` threshold (range `0.086987–0.867071`). The predeclared 50% utility gate therefore failed. Decision: `HOLD_MODEL_NO_SAFE_UTILITY`; no threshold or training tuning was attempted. This is not evidence for deployment and does not establish that other learned gates cannot work.

## Formal evidence

- Source freeze branch `research/local-relevance-x11-gate-4802-20260927`, commit `2697350a93eb3f7594bd670ffaa50f7cc25b2acc`, based on main `609787159651da728b6a9158ed1ec052c77a897a`.
- Corrected capture blob `528d015b5d422633c3c2c7814e31fa626e77ff9e`; smoke blob `9822843d41af0322f22e394ca51d02acedd1e8b5`; reused learner blob `9deb0325b54b2818e8463722078ab547b132ed52`; reused independent auditor blob `3f0f572c8bffa8f5f6415431f2a2ed18435a5c45`.
- Pre-capture smoke: `PASS_X11_API_SMOKE`; 320×240 Canvas XGetImage; depth 24, visual 33, 32 bpp, 307,200 bytes; no file/data output and no model call.
- Capture: one local `codex-x11-preflight:local` container, image ID `sha256:a27c1782065d2240547482d4e0327d54b1a58cf3e45bf0a0326115822337c48a`, linux/amd64, Xvfb display `:177`. Native Tk Canvas XID 2097162. 120 pairs/240 raw frames; 80 training pairs from families 0–3 and 40 held-out pairs from families 4–5; each family has 8 irrelevant, 8 relevant, and 4 critical updates. Exact raw format: 320×240, depth 24, 32 bpp, byte-order 0; 307,200 bytes/frame, 73,728,000 raw frame bytes total.
- Fit/eval: one `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime` container, ID `sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`; CPU, CUDA unavailable, 1 thread, seed 2188, 234 parameters, Adam 0.01, 120 steps; fit time `2.1333815559992217` seconds. Model SHA-256 `42af6e7667a68cd5391d3ff9e3abeb7e44aaa10a2b1af9df7e3df8b3c0a40d5f`.
- Independent audit ran once in a separate network-disabled, read-only-root Docker container. It verified all 120 pairs, decompression and SHA-256, 73,728,000 raw bytes, family split, labels against exact changed-pixel/task-or-critical ROI oracle (0 mismatches), all per-row decisions, and mutation controls (missing/stale/ambiguous yield, critical override, threshold mutation) passed. The auditor emitted `FAIL_RAW_AUDIT` solely for `irrelevant_utility_below_50_percent`; integrity and safety checks passed.
- Held-out: 24/24 relevant or critical forwarded; 0 false suppressions; 8/8 critical forwarded; 16/16 irrelevant forwarded (0 suppressed); irrelevant class `p_irrelevant` min/median/max `0.086987/0.477460/0.867071`; relevant class max `0.000169`.

## Preservation and boundaries

The prior #4799 STOP remains unchanged: its two invocations failed before any XGetImage call (first an existing output mount path; second the invalid `Display.allowed_depths` lookup). No frame, model, or fit resulted there. The corrected #4802 source and a no-write X11 smoke were frozen before its single formal capture. All #4802 data, fit, and audit outputs are retained separately; no retries, alternate seed, threshold edits, GPU, network, package install, user data, runtime edits, or external model provider were used. No runtime/product path is changed.

Limit: this is a small authored synthetic Tk/X11 study on six layouts, one seed, and one local Xvfb format. It says nothing about real applications, arbitrary UI relevance, user tasks, safety, production performance, or generalization beyond these fixtures.

