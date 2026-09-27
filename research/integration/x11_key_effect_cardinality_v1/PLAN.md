# Issue 4032: live key command/state/effect cardinality

Source-freeze successor to closed #1001, related #651, #5 and #57/#2789. Preserve old results. Only research/integration/x11_key_effect_cardinality_v1/ changes; no shared runtime, workflow, roadmap or another worker's path.

## H
Repeated down and distinct taps can have equal completed down-request counts but different sampled X-server key-state transitions. One long held key can insert multiple characters with autorepeat enabled despite one explicit down. These are protocol/application-boundary measurements, not a new OS theorem. Duplicate-down character count is descriptive, never tuned to pass.

## T
One fresh formal allocation key-cardinality-4032-01: two source-frozen ten-case batches, five schedules x two repeat modes x two repetitions, twenty fresh ordinary Tk Entry processes. Batch 0: OFF then ON, NO_INPUT/SINGLE_TAP/DUPLICATE_DOWN/TWO_TAPS/LONG_HOLD. Batch 1: ON then OFF, rotated SINGLE_TAP/DUPLICATE_DOWN/TWO_TAPS/LONG_HOLD/NO_INPUT. Formal letter a; excluded construction letter c. Short down/gap 40 ms; long hold 650 ms; XKB repeat delay 250 ms, interval 50 ms with actual successful readback. No parameter tuning, replacement or consumed-batch rerun.

Private authenticated Xvfb, TCP disabled. No inherited display, user data, clipboard, game, model/provider or experimental network. Supplied Linux x86_64 container / CPython 3.13.5; no available Docker/Podman CLI or image identity, so no Docker/OrbStack replication claim. This is local environment scope, not fleet unavailability.

Independent controller X11 connection subscribes to native key events on the fresh Entry. It sets exact native Entry focus during preparation, emits native XTEST plus sync, records before/after keymap snapshots, then publishes a property-event barrier on the same server connection. The receiver's ordinary Entry class binding performs text insertion; the final bindtag records values after that binding. After the native barrier, a pipe finish command causes an 80 ms deferred final observation and process exit. Audit requires exact native/Tk KeyPress time/state ordering and every Tk KeyRelease as an ordered subsequence of the native release stream. All additional native releases are retained and separately counted, not classified as hardware edges. The construction-only stronger release-equality audit failed on additional leading native releases and is preserved; their cause is not established. No missing press is presumed processed merely from idle or exit.

This implements the same two-line XTEST primitive reviewed in input_owner_v10, not that complete owner, lease admission, watchdog or public CLI. No production bug or drop-in implementation is claimed. Existing #1001 pinned owner blob: 341b3c01649943ddaad5f28431a792c4889cc36e at 4b106a9b549fc3499d39ef2c7e3367d95a6c736c; current main source was reviewed but the full owner is not vendored or executed.

## D
Require complete 20 cases, unchanged source/environment commitments, exact schedule/source/process/clock/byte reconciliation, successful observed app/server/outer exits, neutral terminal AND cleanup keymaps/buttons, original focus and readback repeat mode. Single taps insert one a, distinct two taps insert aa, no-input inserts none. Duplicate-down has two completed down requests but one command-boundary sampled UP-to-DOWN transition. Long OFF inserts exactly one; long ON inserts more than one. Native and Tk journals and final values must reconcile. The exact enabled repeat count is not a gate.

PASS_KEY_STATE_EFFECT_CARDINALITY_BOUNDARY_SCOPED only with all integrity and scientific gates. Valid gate contradiction is FAIL_KEY_STATE_EFFECT_CARDINALITY; absent/corrupt/nonzero-exit evidence is HOLD_EVIDENCE_INTEGRITY. Stop and retain first failure; never substitute rows. Separate raw-only implementation/process, same author not independent human review; 12 semantic mutations update duplicated stdout then must still reject. Four unittest methods exercise ten positive construction cases, twelve negatives and malformed/extra-command cases.

## Analytical interpretation and units
Let D be completed explicit down calls; E the count of those calls with before=UP and after=DOWN at XQueryKeymap snapshots; P the native KeyPress count before the final native barrier; V the final Entry character count. Each is dimensionless, with a different denominator and evidence source. The controlled fixture checks V=P and tests whether D=E=P can be assumed; no interpolation supplies missing state history.

Clock fields ending _ns use time.monotonic_ns within this boot; before/after intervals explicitly bracket native calls. x_time is a uint32 X-server millisecond timestamp. Cross-domain subtraction is forbidden. Measured E is only command-boundary sampled transition count, NOT total continuous X state history, physical hardware edges or duration of useful control. All native events were acquired before the final barrier; the later observation cannot prove other applications consumed them.

## C / U
One ASCII letter, one ordinary Entry binding, one configured Xvfb/Tk stack. No IME, keyboard-layout/modifier changes, raw device, other app/game, arbitrary task correctness, model benefit, time/token savings, production adoption or reliability-frequency claim. Neutral input does not reverse text effects. Source/code hashes establish integrity, not independent trust. End-to-end integration and the global roadmap remain open.

## Roadmap and handoff
Read lineage/current ownership -> retain excluded construction -> freeze and publicly commit readable source and gates -> run batch 0 once then batch 1 once only if batch 0 succeeds -> raw-only audit and twelve corruption controls -> preserve all evidence in one additive PR -> inspect exact-head checks/review -> permitted main merge/readback -> remove only this branch after no dependency remains. No new wrapper-successor Issues.

## Construction audit refinement, before formal
The first audit added a release-equality condition beyond the original Issue. It rejected eight valid input-bearing construction rows. No live run was repeated to repair it. The final auditor preserves both complete streams, requires exact press matching and ordered release inclusion, and reports the difference. This is a declared preformal measurement projection; no row/event is deleted. XKB documents client-specific detectable-autorepeat representation, but that fact does not prove the cause of the observed leading release. Reference: https://www.x.org/archive/X11R7.7/doc/libX11/XKB/xkblib.html (Controls for Keyboard Repeat).
