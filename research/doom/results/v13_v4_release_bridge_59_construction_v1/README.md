# Issue #59: V13-to-V4 release-batch bridge (superseded source snapshot)

This package preserves the initial V13/V11-to-V4 adapter construction against source baseline `2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0`, before PR #7513 and #7515 reached main. Current-source follow-up is [A01](../v13_v4_release_bridge_59_current_main_a01_20261004/README.md); this package remains historical and does not qualify the integrated current-main stack.

## H/T/D/C/U

**H — Hypothesis.** A V13/V11 `input_release_rpc` receipt can be retained while the V4 wrapper receives the `None` result its V3 parent requires, then joined to the V4 transition and owner-thread key-up receipt. Mismatched or missing RPC evidence must fail closed.

**T — Test.** The exploratory `bridge-probe-01` used source snapshots pinned to the then-current `main` and PR #7429/#7449/#7488. Its four test methods included four backend/receipt matrix cases through two release-batch consumers and independently audited one synthetic saved row. The later `bridge-probe-02` attempted a frozen replay but the launcher looked for the freeze in `source/`, so its source preflight did not run.

**D — Outcome.** `bridge-probe-01` is an exploratory construction pass (4 unittest methods, 18 saved-row checks), not a pre-frozen accepted Issue run. `bridge-probe-02` is preserved as `UNQUALIFIED_LAUNCHER_PRECHECK_PATH_ERROR`; its later successful tests do not repair that run's failed preflight. No run in this package is accepted as current-main Issue evidence.

**C — Competing explanation.** The adapter-level pass can hide import, scheduling, backend integration, X11, or packaged-session incompatibility.

**U — Uncertainty.** Fake base-owner call and state sample only. No X server, physical input, app, game, model, scorer freshness, recovery comparison, or live allocation was used. WSLc was unavailable; the native Windows results are host-limited.

## Preserved records

`runs/bridge-probe-01/` retains the exploratory test, trace, audit, and retrospective protocol note. `runs/bridge-probe-02/` retains the frozen command, test/audit output, and launcher-path error. `SHA256SUMS.txt` covers package files except itself, generated Python cache, and `.pyc` files. No raw outcome was overwritten or relabeled.
