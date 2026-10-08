# A08 preregistration — owner close after one real Xvfb hold

**H.** Exact main owner v12 composed through transition v4/v3, with V10 compatibility dependency available, after admitting `a` to a focused mapped Xvfb client: wrapper `close()` delivers one matching KeyRelease, yields owner_release reason `close`, verified true and no keys down, closes/stops thread, and observer keymap says up.

**T.** One TCP-disabled Xvfb `:130`; map/focus a window, down `a` via V4, record KeyPress, close the wrapper, observe KeyRelease and keymap, retain inner owner records/thread flags and Xvfb exit.

**D.** PASS_METHOD_SCOPED requires exact event pair/key/window, server up, verified empty close record, closed/stopped/not-alive owner and Xvfb exit0. Mismatch FAIL; incomplete/setup/cleanup STOP. One candidate invocation; one raw auditor; no retry/overwrite.

**C.** Exact current-main V12/V4/V3/V10 production code, isolated Xvfb, minimal lease; no game/model/desktop app/physical input or private lane.

**U.** One synthetic shutdown path only; no physical state, app consumption, gameplay or performance inference.

Base main `ff13baf57d5f1c12819151e668b92cb6db4a7c1c`.
