# MAP01 v39 Xvfb per-key release identity A02

Issue #59. A02 tests whether the current-main V4 retained-input backend and V3/V10 InputOwner can correlate every per-key admission and release receipt with the exact KeyPress/KeyRelease delivered to the intended Xvfb client. This is a construction boundary only; it is not the required live threat exposure or MAP01 attempt.

## H / T / D / C / U

**H.** The exact `research/doom/doom_retained_input_backend_v4.py` and `research/live_control/input_transition_owner_v3.py` + `input_owner_v10.py` from the current-main freeze will yield 40 ordered admissions and 40 per-key release receipts. Each release will join one exact `(executor id, step, admission_position, key)` admission, and all 80 routed X key events will reach only the frozen focused test window in the expected order.

**T.** In one new network-isolated OrbStack Ubuntu 24.04 arm64 guest, run one Xvfb server and one client window. Call the frozen backend's actual `raw()` method through one executor shim for ten repetitions of the eight-edge sequence `a down/up`, `a down/up`, then `a down`, `space down`, `space up`, `a up`. Capture the X server keymap after each edge, routed event window/type/keycode/order, all emitted admission/release rows, empty owner state after each release batch and close, and Xvfb shutdown. Use an explicit selective host mount for frozen source and a separate host result directory; copy source into the guest's ordinary home before running it. The candidate makes no network calls.

**D.** `PASS_METHOD_SCOPED` requires the frozen bundle hashes, exactly 40 ordered admissions, 40 release receipts and 80 correctly targeted client events, exact identity/key joins, the expected server keymap sequence, complete 1/1/2 per-key release batching per cycle, false authority fields, verified empty release/close, a stopped owner thread and stopped Xvfb. Any complete evidence mismatch is `FAIL`; failed transfer, dependency setup, missing trace, or incomplete cleanup is `STOP`. Candidate invocation: once; raw-only auditor: once after the candidate. No retry.

**C.** The exact integrated `Backend.raw()` path, current-main InputOwner v3/v10, XTEST dispatch, X server keymap, and one focused Python-Xlib receiver are exercised. The executor parent and lease are a small shim so this construction isolates the dispatch and receipt join. No Doom, gameplay, model, controller wait, physical device, or task feedback is exercised.

**U.** One short synthetic episode can establish only that these source versions correlate their receipts with a local Xvfb client. It says nothing about game-level key state, useful feedback, threat response, bounded recovery, survival, MAP01 completion, or the live Issue #59 exit condition.

## Isolation and custody

The previous A01 package retained a STOP because `orbctl push` cannot transfer data into an integration-disabled guest. A02 changes the transfer mechanism: OrbStack's creation-time selective mount exposes only the frozen `SOURCE/`, `RUNNER/`, and unique `results/` directories. The candidate executes from a guest-local copy of source, while raw and audit outputs are written to the separately mounted host result directory. The old A01 STOP and earlier Xvfb timing outcomes remain unchanged.
