# A07 preregistration — real Xvfb held-key shutdown

**H.** Exact current-main InputOwner v12 under transition wrapper v4→v3, after admitting `a` to one focused Xvfb client, will on `owner.close()` deliver one matching KeyRelease, record terminal `owner_release` with reason `close`, `verified=true`, and `keys_down=[]`, and stop its thread; an observer query will show `a` up.

**T.** One TCP-disabled Xvfb `:129` run. Create/map/focus one window, submit one `a` down through V4, verify its client KeyPress, call V4 close, verify the client KeyRelease, sample server keymap, retain V12 records/thread flags and Xvfb exit.

**D.** PASS_METHOD_SCOPED requires frozen hashes, exact press/release event pair at the intended window/keycode, observer key-up, verified terminal close receipt, owner closed/stopped/not alive, Xvfb exit 0. Complete mismatch is FAIL; incomplete/setup/cleanup error is STOP. Candidate once; raw auditor once; never rerun/overwrite.

**C.** Exact current-main owner code on synthetic X server, no backend/game/model/desktop app/physical input/private lane. Lease is a minimal test value with observed focused window ID.

**U.** Establishes only one actual Xvfb shutdown path. No physical-state, target-app consumption, game, scheduler distribution, or latency claim.

Base main: `ff13baf57d5f1c12819151e668b92cb6db4a7c1c`.
