# #1847 O4 X11 pixel VERIFY transfer — retained formal execution stop

Task: `OBSERVATION-GATING-O4-X11-PIXEL-VERIFY-R1-20260919-001`

Disposition: **`STOP_FORMAL_OUTER_TIMEOUT_NO_RESULT` / scientific `NONE`**.

## What completed before formal

The live evidence substrate was eligible in excluded construction:

- three fresh Xvfb signature probes reproduced exact GREEN / RED / GRAY ROI hashes;
- seven fresh construction sessions passed one case for every frozen class;
- candidate/oracle mismatch 0;
- local resolutions 2, required escalations 5;
- lineage-blind unsafe discriminator 3;
- current pixel agreement 7/7, verifier signatures 6/6, stale final RED 1/1, cleanup 7/7;
- descriptive construction verifier p50 / p95 / max = 2.008 / 2.276 / 2.276 ms.

The first manual construction probe had previously stopped before scientific rows because python-xlib looked for a missing default Xauthority file. That harness failure is retained in `DEVELOPMENT.md` / `SOURCE_MANIFEST.json`; it was repaired pre-freeze with private `Xvfb -ac -nolisten tcp` plus one fresh empty explicit XAUTHORITY file per session.

## Frozen formal stop

After source bundle remote readback and ownership reread, the exact frozen monolithic 56-fresh-session formal process was started once. The outer execution wrapper terminated it at 120 seconds before `FORMAL_RESULT.json` was written.

- formal invocations: **1**;
- reruns / replacements / tuning: **0 / 0 / 0**;
- durable formal rows: **0**;
- formal result: **absent**;
- stdout/stderr captured by the outer wrapper: 0 bytes / 0 bytes;
- no runner, fixture, or formal Xvfb process remained after the wrapper stop;
- no case-local Xauthority file remained.

The frozen runner serializes the formal result only after the complete schedule, so already-executed in-memory cases cannot be recovered or used scientifically. No partial-case count is inferred from elapsed time.

## Integrity

Post-stop SHA-256 checks of all five reconstructed frozen source members match `SOURCE_MANIFEST.json` exactly. The source bundle and construction evidence remain unchanged.

## Interpretation / successor boundary

This is an execution/retention stop, not evidence for or against the O4 live-transfer hypothesis. Do **not** rerun #1847.

A legitimate successor may change exactly one harness factor: formal execution/durability packaging. It should preserve the #1847 category corpus, eight repetitions per category, fixture, X11 signatures, gate semantics, schedule order, and decision gates, while serializing immutable small batches so a wrapper stop cannot erase the entire allocation.
