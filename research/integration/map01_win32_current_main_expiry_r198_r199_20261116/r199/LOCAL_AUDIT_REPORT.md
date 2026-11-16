# R199 current-main live-control verification — 2026-11-16

## Outcome

R199 **passes the frozen scoped expiry/recovery/effect checks** against current main. Unlike R198, the frozen query projection agrees with the public runtime result. This is one MAP01 live-control replication, not a whole-task success claim or an integrated efficiency comparison.

- Attempt: `map01-native-expiry-delayed-input-r199-20261116`; one dispatch, one recovery; no replay.
- Source: main `86a52662dc2bb690dd670d52ea8d97816aef2a26`, tree `c35b16d1df4f2e7c6b70a09e2ec672043ace5335`; 11 runtime files hash-pinned. Frozen conditions SHA-256: `a692285d1a4077e6db4e16198d0a40b5e20cfb670fbe85e2732291322b02885a`.
- Read-only preflight: Python, clock, source/assets hashes passed; display 1920×1080; no existing GZDoom process; persistent custody clear/no pending at revision 976.
- Computer Use passively confirmed the unique target and pistol HUD at both gates. Start ammo 50, recovered ammo 49; before/after target window, foreground/root HWND and PID matched their attempt receipts.

## Result

- One click effect was observed: dedicated calibrated ammo panel `50 → 49`; single-click classifier `True`. One later click was scheduled beyond lease expiry and excluded. The source action status/release projection matched frozen values: `recovered` / `True`.
- Native LEFT button-up SendInput returned count 1; SHIFT key-up had its own returned count 1; neutral readback confirmed both released.
- Expiry to supervisor release receipt: 32 ms (limit 1000 ms). Integrated late-input horizon passed for 75 observations over 2 s; max gap 32 ms. Independent neutral horizon: `VERIFIED` for 2 s.
- **`task_success=null`** and replay remains disabled. The current runtime does not claim semantic task success from recovery alone; the verified fact here is the independent single-shot ammo effect.
- Broad upper-client pixel oracle: 293 / 1003200 changed (0.02921%), below its strict 5% threshold. This broad-scene result was not used to override the dedicated ammo-panel classification.
- GZDoom exited normally without forced termination; custody postflight is `clear` / pending=null at revision 985; no GZDoom process remained.

## Preservation

- Raw trial: `trial-raw/` (225 files, 11,097,857 bytes).
- SHA-256 manifest: `RAW-MANIFEST.json` (`847ef60ed0ba0c308b7ba36d7b5926c06df2484f31ccc16e672058de3234e264`).
- Independent machine-checkable adjudication: `INDEPENDENT-ADJUDICATION.json` (`378f8270bf5e89afc5708363677b4aea834f413aad49ef68e051365e8a39c5b5`); full frozen scoped pass `True`.
- Preregistration and conditions: `PREREGISTRATION.md` and `conditions.json`.
- R198 remains separately retained as a partial observation with its stale query projection; it was not replayed or overwritten.

## Remaining work

The R199 pass closes one live recovery/effect slice only. It does not supply model/provider tokens, cold/warm/invalidation/repair arms, matched correctness/latency across approaches, or total integrated resource cost. Issue #57's broader integrated comparison remains open, so the computer-control goal stays active. The closest route baseline remains R237–R240 (ABBA, direct median 3.080 s, compiled 3.440 s; compiled +11.7% at n=2 descriptive medians, no provider calls, outer lifecycle excluded). Next, add matched model/provider cold/warm/invalidation/repair and all-attempt lifecycle accounting; do not describe R199 alone as a speedup or full system completion.
