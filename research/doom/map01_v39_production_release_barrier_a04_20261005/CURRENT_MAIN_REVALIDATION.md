# A04 current-main evidence revalidation

## H — Hypothesis

At the V13 terminal-release boundary, draining deferred per-key release measurements before terminal can recover a bounded actuation-matched receipt that the exact baseline leaves unavailable.

## T — Local checks

- Current main: `d3a51bc4c962b223d05280225042b96a033df8bf`.
- All 14 external source-lock paths match their recorded SHA-256 on current main; all 15 package-owned paths in the manifest also match (29/29 total).
- Three-case fake-Xlib unittest suite passed locally on Python 3.12; static byte-compilation passed.
- Raw-only auditor returned `PASS` for all three retained cases.
- The container gate remains STOP. No image inventory retry, pull, build, or container run was attempted.

## D — Scope

The preserved A04 experiment is single-key (F8) synthetic host-Python evidence. It compares the exact candidate baseline, late-resample treatment, and an unavailable retry sample. No real X11/display/GUI/game, OS input, application effect, model, stale-policy behavior during model wait, MAP01 result, or live allocation was exercised.

## C — Conclusion

PASS only for the narrow single-key fake-Xlib terminal-release ordering probe. Container validation remains STOP, not PASS. No production or physical-release claim follows. Preserve as draft pending independent review.

## U — Explicit gap

The PR review identified that the passing A04 schedule admits one key and does not measure multi-key inter-release query ordering or cost. The separate #7878 baseline does not exercise this per-key-resample treatment. A distinct two-key candidate trace remains required; do not infer that gap is closed by these three cases.
