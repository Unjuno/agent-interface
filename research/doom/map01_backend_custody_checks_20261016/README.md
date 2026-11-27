# MAP01 backend custody across Executor replacement

Main base `83713325d5248cf9c62430154bb5a701a7663e1a` retained unverified
release obligations in each Executor, but replacing that wrapper lost the fence.
The first selected Fake X RED holds native KeyRelease send with keycode 38 down.
After the original failed terminal and `Executor.close()`, a second Executor on
the same backend accepts an observation-only intent and replaces `backend.lease`.
The original obligation still exists only in the old wrapper. The retained JSON
row shows accepted replacement, changed lease and `native_resumed=false`.
No second positive input is submitted or claimed.

## Adopted behavior

The MAP01 release-batch backend now owns an RLock-protected opaque Executor
token and a copied first unverified-release obligation. The process-identity
backend inherits this custody. V12 claims it at construction when these hooks
are provided; V13 inherits that behavior. Two Executors cannot attach to that
backend concurrently, including between programs. Failed construction creates no
new execution worker and cannot change the original lease.

The Executor retains the original obligation in backend custody before external
terminal publication. It releases its custody only after a successful close has
no active intent, no unverified obligation, and has joined its release watchers.
Repeated healthy close is idempotent. Verified healthy cleanup followed by close
permits a replacement to execute from a fresh observation. Failed/ambiguous
cleanup keeps custody occupied after close; late native completion, empty fake
key state or a fresh observation does not erase the first obligation. Snapshots
copy the evidence and do not grant input authority. Missing/wrong owner tokens
cannot release or rewrite custody.

Generic backends without these optional hooks retain their prior per-Executor
behavior. This changes MAP01's release-batch/process-identity path, not all public
interfaces or a global resource registry. It adds no automatic recovery/retry.

## Checks and retained raw

Five new methods cover stalled native release and refused replacement, sticky
custody after late owner return/fresh capture, idle double attachment, two healthy
programs across closed Executors, concurrent constructor claims, copied snapshots,
wrong/None tokens and idempotent close. The native fault uses actual selected
capture/backend, Executor/V4/V12 and Fake X. Its JSON rows retain the original
token/deadline/sequence/process-source/release batch, held key and eventual fake
neutrality without resetting custody. This is no live GUI or physical release.

The first broad run has three setup errors in preexisting partial
`__new__(V15Backend)` fixtures. Those fixtures now initialize the constructor's
custody lock/owner/obligation state; all existing explicit-UP/cancel/batch
assertions remain unchanged and the seven-method module passes. The original
failed run and first repaired output are retained. No runtime fallback silently
creates or resets custody on an incompletely initialized backend.

Clean tested source `8008eae3975309c089ddf2876c63e2767cbf6577`: normal and
optimized Python each pass 52 isolated modules / 381 methods, zero failures,
11 skips (370 executed). Skips are the optional real-Codex handshake and ten
host-inapplicable POSIX conditions. Bounded read-only review independently passes
the five custody methods and seven repaired-fixture methods in both modes.
Source/status summaries and every log remain under `normal/`, `optimized/`,
`intermediate-normal/`. Commands use `../check_map01_control_regressions.py
--output-dir <fresh path>`, adding `--optimized` for the second mode. Host: Windows,
Python 3.13.14, python-xlib 0.33, Pillow 12.2.0, MCP 1.30.0, openpyxl 3.1.5.
`MANIFEST.json` hashes the packet. These are ordinary regression checks; no
historical producer or consumed formal allocation reran.

## Remaining boundaries

Custody lasts for this backend instance in this Python process. Constructing a
different backend for the same physical endpoint, losing the process/host, or
replacing the input owner requires an external, qualified authority/recovery
protocol. This patch neither implements nor certifies that handoff. Trusted
local lifecycle hooks are not a protection against arbitrary Python mutation.

Input send/sync/readback, close/join, scheduler/GIL, durable custody and physical
release are not proven hard-time bounded. Test-owned native-gate resumption is
cleanup, not finite task recovery. Window incarnation, independent task effects,
cross-process replacement, successful recovery and matched efficiency remain open
in #17/#59/#57. No real GUI/model/game/WSL/container allocation was launched;
optional remote CI is not claimed passed.
