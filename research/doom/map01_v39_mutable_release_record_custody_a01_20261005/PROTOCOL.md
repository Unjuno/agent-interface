# Mutable owner-release record custody A01

## H / T / D / C / U

**H.** On the frozen PR #7805 V13 owner / bridge V2 source, if the per-key post-release sample is unavailable but the later aggregate keymap proves neutral, a bridge drain while that same `owner_release` record is still partial advances its index cursor. The subsequent in-place `verified=true, keys_down=[]` mutation is then skipped, leaving the bridge-held ledger stale. A one-variable diagnostic probe that revisits final neutral state should clear only that ledger without inventing a confirmed per-key key-up or duplicating receipts.

**T.** In an isolated fake-Xlib harness, admit F8 and confirm its synthetic down. During owner cleanup, inject one keymap sampling exception specifically for the per-key post-release sample. Gate the subsequent aggregate pointer query after the owner has appended its mutable partial record. Drain the bridge at the gate, then unblock aggregate verification, wait until the same record mutates to verified-empty, and drain again. Run the identical schedule once against the frozen bridge V2 and once against a diagnostic subclass that remembers emitted per-key row counts but revisits monotonic verified-neutral state. Preserve both raw outcomes.

**D.** Baseline reproduces the hypothesis iff at-gate record is unverified with one unavailable per-key sample, cursor advances, final owner record becomes verified-empty and fake physical state is empty, yet bridge-held F8 remains after its second drain. Probe passes iff final bridge-held is empty, exactly one original unavailable measurement is emitted, no `CONFIRMED_PHYSICAL_UP` is fabricated, and owner/fake physical state is neutral. Any source mismatch, missing synchronization gate, unexpected row/identity, timeout, or output collision is STOP (candidate execution count zero for preflight STOP).

**C.** This is one deterministic synthetic fake-display schedule with fault injection. Aggregate neutrality does not identify the exact physical up edge. The local subclass is a diagnostic probe only; it is not production code and does not establish an adequate production protocol.

**U.** No live X11/keyboard, application/game consumption, useful feedback, bounded recovery, threat-control, matched task effect, latency distribution, safety, or Issue #59 completion is tested. No live allocation is granted or consumed.

## Freeze

- Base main at start: `4a8049327eb44b54cfcf55167adb102a710a7051`.
- Exact frozen candidate bytes: PR #7805 `input_owner_v13_candidate.py` SHA-256 `0e3c65aadfba76b644f1ca99afa267bc873bc120320a4b0cac67dafb82cfa814`; `bridge_v2_candidate.py` SHA-256 `81e759b0484ac5b7854da0ebcffa917035f56b83a3dbfda40cafbb7f9f5138d1`.
- A01 run ID `MAP01-V39-MUTABLE-RELEASE-RECORD-CUSTODY-A01-FORMAL-01-20261005` stopped at Docker CLI image parsing; container starts and candidate executions were both zero. The exact command/error are retained in `STOP_A01.txt`.
- A02 run ID `MAP01-V39-MUTABLE-RELEASE-RECORD-CUSTODY-A01-FORMAL-02-20261005`: baseline and one-variable probe, one invocation each, same deterministic input/fault/gate sequence. This is a separately labeled fresh run after a pre-container wrapper STOP, not an overwrite or silent retry.
- A02 output is write-once under `results/formal_02/`.
- Container: locally cached `python:3.12.11-slim@sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f`, `linux/arm64`; no network, read-only repository bind except this package's result directory, one CPU, 1 GiB memory, 64 pids.
- Stop before either candidate run if frozen source hashes mismatch, output exists, source/harness import fails, or gate protocol cannot be established. Do not silently alter fault indices or retry.
