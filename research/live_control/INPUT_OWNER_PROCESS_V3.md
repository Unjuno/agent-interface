# Explicit owned owner service v3

An explicit `cancellation=True` launch now adds the independently serviced
[cancellation lane](INPUT_OWNER_CANCEL_V4.md). Default launch and standard backend
selection remain unchanged; the original packet below qualifies its pinned code.

`input_owner_process_v3.launch_owner_service(display=..., out=...)` places the
current strict transition/native owner and RPC v2 in an independently spawned
Python process. This is an explicit library API; it does not select or replace
the standard MAP01/session backend. The caller must already own the authorized
display. Tests supply the named Fake X factory and exercise no real display.

The returned handle exposes a copy of accepted startup metadata, its exact owned
`multiprocessing.Process`, `take_socket()` once, `close_channel()`, `wait(timeout)`
and `saved_files()`. The socket may be transferred to one owned client process.
Startup binds the private handshake to file bytes, fresh logical generation,
owner ID, actual PID/PPID and supervisor/owned-process lineage. This is not an OS
PID creation-time guarantee. No automatic process kill, replacement or retry is
performed. A startup exception retains `owner_service_handle`; ordinary startup
errors also expose `ServiceStartupError.handle`. Even pre-Process allocation
failure returns inspectable unverified custody and closes acquired descriptors.

The service handles client EOF by closing the same owner. It publishes initial
recovery and waits for the same unresolved owner thread before leaving its
context, including when recovery publication fails. Parent `wait(timeout)` stays
finite and reports an alive/unverified service. Initial unverified recovery is
immutable; late settlement cannot upgrade it. A verified final result requires
consistent startup/recovery/finish bytes, successful context exit, stopped owner,
and exit0 of the exact owned process. Complete files while that process remains
alive are insufficient. Service death or missing records remains unverified.

Files are exclusively published via hard links from file-fsynced temporary bytes;
existing results are never replaced. Directory fsync is requested on POSIX.
Windows directory and power-loss persistence are unqualified. Export preserves
the exact bytes and SHA256 from one read. These are testable publication contracts,
not a guarantee against arbitrary storage failure or supervisor/service death.

[Evidence and first failures](../integration/owned_owner_process_v3_20261016/README.md):
normal/-O each55 methods,13 process/inert rows and26 selected RPC regression rows.
Native input, physical release latency, shared-input arbitration, real task
effects and matched economics remain unqualified. The next integration under#59
is a selected backend/Executor custody adapter with cancellation/telemetry and
actual controller/session failure. RPC v2 close returns a receipt and is not a
drop-in replacement for all existing owner interfaces.
