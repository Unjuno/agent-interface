# Issue #6501 C01 control-state qualification review (2026-10-08)

## H / T / D / C / U

- **H:** Does the retained C01 run establish that the `Event.wait` negative control was blocked when `GetThreadIOPendingFlag` was sampled?
- **T:** Inspect the immutable source and retained records from PR #7089 / rescue PR #8316. Do not rerun the consumed Windows allocation or alter its archived bytes.
- **D:** This additive static requalification record. The original 33-file C01 packet, its manifests, raw outputs, and the original `PASS_OWNED_THREAD_PENDING_METHOD_ONLY` record are unchanged.
- **C:** `probe.py.txt` signals `wait_enter` immediately before calling `wait_release.wait()`. The main thread proceeds after observing that signal, then samples the waiter handle. There is no acknowledgement or other retained evidence that the waiter had entered the blocking call before those samples. A runnable waiter and a waiter blocked in `Event.wait` can both report `pending=false`. Therefore the three raw `(reader_pending=true, control_pending=false)` pairs do not establish the claimed blocked-control contrast. The records still preserve the observed API values and the normal read/cleanup sequence; the ten saved-audit corruption rejections concern serialized-data integrity, not this missing synchronization fact.
- **U / disposition:** `HOLD_CONTROL_STATE_UNESTABLISHED`. This is a qualification HOLD, not a contrary Windows API result and not evidence of cancellation efficacy or failure. The C01 archive is useful as an unchanged one-shot record of sampled values, but its `Event.wait` negative-control interpretation and method-pass status must not be promoted. Do not replay the consumed allocation. A future comparison needs separately authorized, fresh evidence that the control reached the state claimed by its protocol.

## Source anchor

- Original PR #7089 head: `55bc91e0e27ff95177a64cf9d582ac7603c90da0`.
- Current-main custody rescue reviewed: PR #8316 head `94d452c5a892b2e63a8afd72b3a416f69f263953`.
- This review is source inspection only; it introduces no runtime change and makes no application, task-effect, portability, or performance claim.
