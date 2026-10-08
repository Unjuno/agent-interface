# Issue #3944 — observer IPC freshness v3 batched allocation

Allocation: `observer-ipc-freshness-20260926-r3`.
Intake main: `e2be13b9af699cfe9de8cc6d0ce2c32846cb6530`.
Path: `research/live_control/observer_ipc_freshness_v3/**`.

Preserve the original 2026-09-22 preformal STOP and v2 `STOP_OUTER_EXECUTION_TIMEOUT_NO_CHECKPOINT` unchanged. v2 formal rows are unavailable and ineligible. This fresh allocation keeps the scientific matrix and thresholds unchanged; only execution serialization changes to ten immutable four-case batches with per-case checkpointing and retained external batch exits. Each batch uses a fresh private Xvfb, a disclosed scheduling/reset difference; no cross-case state is part of the contract.

## H
At CPython switch interval 5 ms, a separate observer process can preserve a short X11 target capture under a CPU-bound thread in the consumer interpreter, but packaging/pipe/GIL receipt delay may still make that capture old. Capture and conservative receive age are scored separately.

## T
Same 40 cases and order as v2: ten blocks x INLINE_IDLE/INLINE_THREAD/PROCESS_IDLE/PROCESS_THREAD; pulse offsets 50/52/54/56/58 ms twice; 5 ms pulse; 32x32 ROI; 2 ms non-catch-up cadence over120 ms; CPU0 consumer/observer, CPU1 load thread, CPU2 Xvfb, CPU3 fixture; switch interval5 ms. PROCESS uses real subprocess JSONL stdout. Exact ROI bytes retained.

Each block is one bounded invocation. Case result is atomically checkpointed immediately. Batch i requires retained external exit0 from batch i-1. No consumed-batch retry/replacement/exclusion/tuning. After ten batches a read-only assembler makes one 40-case RAW.json.

## D
Same gates as v2. Integrity additionally requires ten batch receipts/external exits and socket cleanup. PASS iff PROCESS_THREAD captures >=9/10, exceeds INLINE_THREAD by >=3 cases, and has a <=5 ms receive-age target in >=9/10 cases. Complete integrity missing these is HOLD_CAPTURE_DELIVERY_GAIN. Scientific contradiction/integrity errors are FAIL/HOLD as typed. Independent raw-only audit and >=10 effective controls mandatory.

## C
Fresh Xvfb per block and process placement can change cache/scheduling; this is not a causal isolated GIL measurement. IPC and X-server scheduling can dominate.

## U
Private synthetic Xvfb pulses only; no model/task/input/token/useful-feedback/release/product/cross-platform claim.
