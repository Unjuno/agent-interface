# #3430 fresh allocation 02 — HOLD

Decision: `HOLD_DECOY_EFFECT_UNVERIFIED`

This is a new allocation, separate from the unretained prior attempt. It does not edit or replace any #3419/#3430 historical report.

## H/T/D/C/U

- **H:** The new raw trace is byte-bound, but the stale/decoy input effects are not fully established. The old X11 window ID was reused by the decoy after generation 1 exited. A direct key send to that ID returned 0 but produced no observed decoy effect. The p2 positive control did produce its expected title effect.
- **T:** One fresh isolated run in `issue3419-multiwindow:20260920` (image ID `sha256:6274b31351429a9cd2385f76c75c2df9f817c3dca6d285f4cd8ccceb88d8d1ad`), with `--network none`, Xvfb :155, Chromium generation 1 then p2+decoy generation 2. The runner sent Return to the old XID, then the decoy XID, then p2; it recorded X11 window/PID and independently observed window titles.
- **D:** `raw.jsonl` is the exact file written inside the run container. It is 831 bytes, four canonical compact-JSON LF rows, SHA-256 `f6dfe6d61b24e4c5f5daa52a80e70e90c602cd4b38cdfb7a870399627d540c87`. A separate `python:3.12-slim` container recomputed the hash and parsed/audited those exact bytes.
- **C:** Byte/serialization gate: PASS. p2 positive control: PASS. Stale attempt caused no p2 effect: observed, but this does not prove an admission-path rejection. XID reuse by decoy: observed. Decoy effect: NOT VERIFIED (send returned 0, title effect absent). Overall: HOLD; do not promote as generation/input acceptance.
- **U:** This fixture does not call the production receipt-admission predicate. A raw X11 send return code is not proof of accepted or rejected application input. No cross-app, product, or performance claim.

## Exact findings

- Old generation-1 XID: 2097155; old window PID: 9.
- Generation-2 p2: XID 4194307; PID 138.
- Decoy: XID 2097155 (the old XID was reused); PID 139.
- Old-XID key send returned 0; neither p2 nor decoy title effect was observed after that send.
- Decoy-window key send returned 0; decoy title effect was not observed; p2 remained unchanged.
- p2-window key send returned 0; p2 title effect was observed.
- Independent audit result: `HOLD_DECOY_EFFECT_UNVERIFIED`; all raw-byte checks passed.

## Provenance and next gate

A preceding attempted allocation's output was truncated and its container had exited before the output could be recovered. It is recorded as `STOP_OBSERVER_OUTPUT_UNRECOVERABLE`, not reused or counted as a PASS. A first audit invocation also used a bad mount path (exit 2); the corrected read-only audit invocation completed in the independent container.

Before another formal allocation, calibrate focus/input delivery in a construction-only probe, freeze the corrected driver and auditor, then run a distinct allocation. To claim a stale-receipt admission result, exercise the real admission/dispatch path; this raw X11 fixture alone cannot do that.
