# Native XInput2 multi-contact lifecycle under finite authority

Task `XI2-NATIVE-MULTICONTACT-LIFECYCLE-20260917-001`, Issue #655, native-X-server Rung-2 successor to #574 and the merged keyboard/pointer result #625/#646.

**Decision: `PASS_NATIVE_XI2_MULTICONTACT_LIFECYCLE_SCOPED`.**

## H
A common finite authority envelope can own two simultaneous touch contact resources on a genuine XInput2 DirectTouch device, preserve distinct server contact identities through partial release, deterministically release all contacts on deadline/cancel, reject stale/out-of-subset proposals without new touch input, and produce an effect that a deliberate single-pointer approximation does not.

## T
Every formal case uses a fresh private Xorg 21.1.16 with dummy video and the upstream `inputtest` Xorg driver configured `DeviceType "Touch"`, `TouchCount "4"`. This path does not use `/dev/uinput` or kernel HID. A separate XI2 fixture window independently receives events. Primary touch evidence is restricted to slave events where `deviceid == sourceid == TestTouch`; construction showed XIAllDevices also delivers a master-pointer copy, which is deliberately not double-counted.

Frozen block: 28 first cases, seven scenarios x four repetitions, seed `5742026091702`, owner deadline 160 ms.

## Formal first result

| scenario | n | pass | slave touch begin/update/end per case | effect/rejection |
|---|---:|---:|---|---|
| pinch_complete | 4 | 4 | 2 / 2 / 2 | pinch effect 4/4; min-distance ratio 0.50 in all four |
| deadline_pair | 4 | 4 | 2 / 0 / 2 | owner expiry releases both; no pinch effect |
| cancel_pair | 4 | 4 | 2 / 0 / 2 | explicit cancel releases both; no pinch effect |
| partial_release | 4 | 4 | 2 / 1 / 2 | surviving contact retains the same XI2 detail through update then end |
| stale_continue | 4 | 4 | 2 / 0 / 2 | delayed update rejected `EXPIRED` 4/4, no update event |
| wrong_contact | 4 | 4 | 0 / 0 / 0 | undeclared third contact rejected `OUT_OF_SUBSET` 4/4 |
| pointer_approx | 4 | 4 | 0 / 0 / 0 | core pointer press/release occurs; touch events 0 and pinch effect 0 |

All 28 cases finish with fixture `active_touch_details=[]`, adapter logical-contact set empty, and pointer neutral. The true two-contact arm therefore differs from the deliberately invalid single-pointer approximation at the independently observed XI2 application boundary.

Construction also established the key identity property used by the formal scorer: the two simultaneous contacts receive distinct XI2 detail IDs; the same two IDs appear in `pinch_complete` begin/update/end. In `partial_release`, one ID ends first while the other remains active and retains its own ID for the later update and end.

## D
`PASS_NATIVE_XI2_MULTICONTACT_LIFECYCLE_SCOPED` under the preregistered gate: 28/28 cases pass and every scenario stratum is exactly 4/4.

## ERROR CHECK
The unchanged frozen auditor reports 28 cases, 28 pass, errors `[]`, all seven strata n=4, and the scoped PASS decision. A separately implemented postformal verifier independently checks frozen source hashes, schedule identity, slave-event provenance, contact identity/order, effect/rejection semantics and terminal neutral state: 28/28, errors `[]`.

Seven deliberate corruptions of copied evidence are rejected by the frozen auditor: missing case; duplicate contact detail; lost TouchEnd; nonempty active-contact terminal; wrong-contact false admission; stale update emitted; pointer approximation containing counterfeit touch input.

One outer-wrapper incident occurred after cases 0–6: an invocation omitted the already-frozen required `--case-id` CLI argument. `argparse` exited before the case output directory/Xorg/task input existed. This was posted to Issue #655 before case 07's first actual instantiation; no experiment source/schedule/gate changed. The original wrapper stderr sidecar was later overwritten by the successful wrapper invocation, so `ORCHESTRATION_INCIDENT.md` is explicitly a reconstructed incident note rather than raw stderr retention.

## C / U
- This is an Xorg synthetic DirectTouch device, not kernel uinput/HID hardware.
- X11/XInput2 only; no Windows/macOS transfer.
- The fixture is a synthetic XI2 recognizer; this is not application task success or productivity evidence.
- The first touch can carry `XI_TouchEmulatingPointer`; the second contact remains distinct. Primary touch scoring is tied to the TestTouch slave source to avoid master/slave duplicate delivery.
- No latency/performance promotion was preregistered.
- The result does not yet prove one high-level semantic gesture can be lowered through two backends under one shared implementation.

## Next rung
Rung 3 should freeze one planner-facing semantic `PINCH` intent and lower it through two already-retained backends — native XI2 `inputtest` and browser/CDP — while holding semantic target/effect/authority fields constant. The question should be backend-independent semantics/provenance, not another touch feasibility sweep.
