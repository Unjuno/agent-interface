# #3430 allocation 04 — FAIL: old XID retargeted current p2 window

Decision: `FAIL_STALE_XID_RETARGETED_CURRENT_WINDOW` (raw X11 XID-only path; not a production guard verdict)

This is a fresh allocation after allocation 03's readiness-audit HOLD. It preserves the earlier raw traces and tests the same direct-X11 stale target only after exact readiness evidence.

## H/T/D/C/U

- **H:** Across the generation-1 → generation-2 transition, an old XID-only target is not a stable authority. If the X server reuses that XID for p2, focusing it and sending input can mutate p2 before a fresh p2 action is issued.
- **T:** One fresh `--network none` run in `issue3419-multiwindow:20260920@sha256:6274b31351429a9cd2385f76c75c2df9f817c3dca6d285f4cd8ccceb88d8d1ad`, Xvfb :158. The runner waited for anchored `^READY-…$` window-name matches and re-read each exact title before recording readiness. It then terminated p1, launched p2+decoy, sent Return to the old XID, tested decoy input, then sent a fresh p2 positive-control input.
- **D:** `raw.jsonl`: 1,493 bytes, five canonical compact-JSON LF rows; SHA-256 `fe01c4be59e4b6dd686ad6c8d7e1b3588f6165e10ffc927a16c99b10b1cb321f`. The separate pinned Python 3.12 audit recomputed this hash and all acceptance predicates from the rows.
- **C:** Exact-byte, exact-ready-title, focus-match, cleanup, decoy isolation, and fresh p2 positive-control gates pass. The old p1 XID 2097155 was reused by p2 (PID 148); after focusing/sending to that old XID, p2 title changed from `READY-P2-3430-04` to `P2-3430-04-EFFECT-1`. A later explicit p2 input independently advanced it to `EFFECT-2`. The independent audit returns `FAIL_STALE_XID_RETARGETED_CURRENT_WINDOW`.
- **U:** This is a counterexample to XID-only direct input after reuse, not evidence that a production composite-generation admission path fails. It does not establish cross-application reliability, human tempo, product readiness, or end-to-end benefit.

## Findings

- p1: generation 1, PID 9, XID 2097155.
- p2: generation 2, PID 148, XID 2097155 (same XID reused).
- decoy: generation 2, PID 149, XID 4194307.
- Old-XID send focused XID 2097155, returned 0, and caused the p2 effect before the later fresh p2 control.
- Decoy input caused only the decoy effect; p2 remained at its stale-input effect count.
- Fresh p2 input caused a second independently observed p2 effect.
- All Chromium and Xvfb processes were reaped; the container exited 0. The semantic decision is FAIL despite clean execution and byte audit.

## Audit correction

The first independent audit of this raw file returned HOLD because its decoy-isolation predicate incorrectly expected p2 to remain at the pre-stale baseline. The exact trace shows p2 had already changed during the old-XID send. The corrected auditor compares the decoy-control observation to the post-stale p2 title, recomputes stale XID ownership against both current windows, and returns the fail above. No allocation was rerun for this audit correction.
