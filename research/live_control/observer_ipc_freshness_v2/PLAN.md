# Issue #3944 — observer IPC freshness v2 allocation

Allocation: `observer-ipc-freshness-20260926-r2`.
Intake main: `3666992ab2b5e1b41b159b361d1c690d8e720fdf`.
Path: `research/live_control/observer_ipc_freshness_v2/**`.

This is a fresh allocation under the same scientific Issue. It preserves the original
`STOP_PREFORMAL_PUBLICATION_BLOCKED` and PR #3959 unchanged. No predecessor formal row exists or is pooled.

## H
At CPython switch interval 5 ms, a separate observer process can preserve a short X11 target capture under a CPU-bound thread in the consumer interpreter, but packaging/pipe/GIL receipt delay may still make that capture old. Capture and conservative receive age are scored separately.

## T
Ten blocks x four arms = 40 fresh pulse cases. Arms: INLINE_IDLE, INLINE_THREAD,
PROCESS_IDLE, PROCESS_THREAD. Pulse offsets 50/52/54/56/58 ms repeated twice;
draw-complete to clear-request target 5 ms. 32x32 ROI, target1024 pixels, native
XGetImage cadence2 ms over120 ms with missed slots skipped. Consumer/observer CPU0,
load thread CPU1, Xvfb CPU2, fixture CPU3. `sys.setswitchinterval(0.005)`.
PROCESS uses a real subprocess stdout JSONL pipe. INLINE serializes and parses the same
JSON record in-process. Exact raw ROI bytes are retained compressed in each record.

## D
Integrity: 40 exact cases/order/affinity/source/exits, nonzero load CPU, final clear,
pulse exposure4–8 ms, reconstructible pixels/timestamps. PASS only if PROCESS_THREAD
captures target in >=9/10 cases, exceeds INLINE_THREAD by >=3 cases, and has at least
one target observation with receive age <=5 ms in >=9/10 cases. Otherwise complete
integrity yields HOLD_CAPTURE_DELIVERY_GAIN. Wrong/incomplete evidence is FAIL/HOLD/STOP.
Independent raw-only audit and >=10 effective corruption controls are mandatory.

## C
Process placement changes address space/scheduling as well as GIL sharing; IPC and X-server scheduling can dominate. This does not directly measure GIL wait causally.

## U
Synthetic private Xvfb pulses only. No model, GUI task, input action, user data,
tokens, end-to-end useful-feedback, release semantics, production or cross-platform claim.
