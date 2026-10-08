# #3430 allocation 03 — HOLD with partial stale-XID effect observation

Decision: `HOLD_READINESS_UNVERIFIED_STALE_EFFECT_OBSERVED`

This fresh allocation is separate from allocation 02 and is not a replacement for any #3419 historical evidence.

## H/T/D/C/U

- **H:** Raw JSONL bytes are canonical and independently hash-bound. A direct input sent to the old XID was followed by a decoy title effect, but the READY condition was not independently established before that event. The result is HOLD, not a formal safety FAIL or PASS.
- **T:** One `--network none` run in the pinned local image `issue3419-multiwindow:20260920@sha256:6274b31351429a9cd2385f76c75c2df9f817c3dca6d285f4cd8ccceb88d8d1ad`. The container used Xvfb :157, Chromium generation 1, then p2+decoy generation 2; after the transition it focused the old XID and sent Return, then exercised decoy and p2 controls.
- **D:** `raw.jsonl`: 1,940 bytes, 5 compact sorted-key JSON rows with LF endings, SHA-256 `86e619f47618a0e1fe160fdcf93396adc9db3268602aba540556adba225a2a9d`. Independent `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` re-read the exact file.
- **C:** Byte gate PASS; cleanup, decoy-control effect, and p2 positive effect PASS. The raw record shows the old XID reused by the decoy and a title change after the stale-XID send. However, the runner's `ready_markers:true` was self-reported; the captured pre-send title contains the literal data URL rather than the exact READY title. The corrected independent auditor therefore returns HOLD.
- **U:** The observed effect is retained as partial evidence only. No production admission predicate, broad GUI, cross-app, product, or performance claim follows.

## Audit correction

An initial audit accepted the runner-supplied readiness boolean and emitted a FAIL label. Review of the exact raw titles showed that this gate was not independently evidenced. The final auditor ignores that boolean, recomputes readiness from the captured window titles, and classifies this allocation as HOLD. The initial label is withdrawn; the raw file is unchanged.

The exact readiness/focus construction probe is retained separately in `CONSTRUCTION_PROBE.md`. Allocation 04 is a distinct fresh run using an anchored regex plus exact window-title equality.
