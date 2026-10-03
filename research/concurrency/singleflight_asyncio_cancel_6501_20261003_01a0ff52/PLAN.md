# Actual asyncio read-only singleflight cancellation boundary — #6501

New allocation `6501-ASYNCIO-ORBSTACK-A01-20261003-01a0ff52-70ab`.
Worker `01a0ff52-70ab-7f10-82b3-e60375a032fb`, FINAL-v5.
Branch `research/6501-asyncio-cancellation-01a0ff52`.
Base `3116528f3abe0fec72cfc1b5b2b5b4b05538512e`.

## H / T / D / C / U (prospective)

H: actual CPython asyncio waiter cancellation can invalidate another caller when
they directly await one producer. Standard shielding separates cancellation, but
plain shielding leaves the shared producer pending after all waiters exit; explicit
last-waiter ownership can cancel this otherwise unnecessary work. All delivery
paths still need a caller-local current-generation check.

T: 2 and 3 callers × six scenarios × four policies = 48 distinct conditions,
120 caller outcomes. Scenarios: stable, first waiter cancellation, last waiter
cancellation, all waiter cancellation, generation change before result, owner
RuntimeError. Policies: independent producer per caller; direct shared await;
`asyncio.shield` around shared await; shield plus remaining-waiter counter and
last-detach producer cancellation. Every producer starts before a barrier opens;
waiters reach their await before cancellation, generation change or producer gate
release. No wall-clock racing/sleep deadline is used; sleep(0) yields one finalizer
cycle. Each row has a 2 s harness timeout, whose expiry fails the allocation.

D: scoped boundary PASS requires all 48 unique conditions, actual producer counts
(callers for independent, one for each shared arm), expected waiter statuses from
the independent raw-only auditor, preserved payload/generation identities, producer
exit receipts, and bounded cleanup of all retained tasks. Required contrasts:
direct shared await cancels unaffected waiters in one-cancel controls; shielding
preserves them; generation-change rows refuse delivery as STALE for every caller;
owner errors produce OWNER_FAILED, never success. In all-cancel rows, plain shield
must expose its one pending producer before harness cleanup; reference-count arm
must cancel it on last detach. All eight effective output corruptions must fail
the raw-only audit. Any disagreement is FAIL/HOLD, not filtered from denominator.
Exactly one candidate and then one separate audit (only on exit 0), retries zero.
Construction mini-checks are distinct and may be repaired before this freeze.

C: the cancellation behavior is a documented Python mechanism, not novel research.
It is tested here as a concrete transfer prerequisite for #6501. One shared result
is descriptive evidence, not independent corroboration, authority or effect proof.
The last-waiter counter assumes one event loop with serialized detach and retained
strong task references; it is not a cross-thread ownership or broker protocol.

U: authored barriers and fixed payload, no external verifier, real GUI, action,
model, task-effect, performance distribution, deadline semantics, ambiguous scope
equivalence, dynamic late joins, noncooperative producer, TaskGroup interaction,
generation ABA or production integration. There are no statistical samples and
no causal latency/token benefit estimate. Historical T0/T0b and #6857/#6858 are
unchanged and not rerun. A portable source is not cross-platform execution evidence.

## Environment and resources

Dedicated guest `research-6501-async-01a0ff52-70ab` (Ubuntu noble arm64), guest-local
Docker only. No shared Mac Docker context restart/repair: its read-only inventory
returned a containerd missing-blob/operation-not-supported error. Own guest setup
installed Docker, then pulled python:3.12-slim; exact image/CPython/source hashes
are frozen in FREEZE.json before candidate. Candidate/auditor containers use
--pull never, --network none, --read-only, 0.25 CPU, 128 MiB memory, read-only source,
one separate writable output, and no GPU/display. Observe cgroup limits inside
each actual container rather than inferring enforcement from flags. Source copies
are checked against the freeze before use; output paths are new/exclusive-create.
The container source/output mounts are inside this guest; there is no host Docker
socket, credentials, personal data or runtime module mount. Terminate only own
guest after output readback and preserve it for reversible recovery.

## Primary reference

Python's [shield documentation](https://docs.python.org/3.14/library/asyncio-task.html#shielding-from-cancellation)
describes separating the outer caller's cancellation from the retained inner task,
while the caller still receives CancelledError, and warns to keep strong references.
The public page is current 3.14 documentation; the exact exercised 3.12 interpreter
is recorded independently in the image freeze. We do not treat documentation as
local measured evidence. No new standard/library abstraction is introduced.

## Fields and units

| Field | Japanese meaning / definition | SI unit | Range / assumptions | Type |
|---|---|---|---|---|
| callers | 同一条件内の待ち手の個数 | 1 (count) | 2 or 3 | exact int |
| seq | 同一行の記録イベントの順序 | 1 (ordinal) | starts at 1, increases by 1 | exact int |
| generation | 記述的な観測結果の世代 | 1 (ordinal) | produced 1; current 1 or 2 | exact int |
| remaining | まだ退出していない待ち手の個数 | 1 (count) | 0 through callers, one event loop | exact int |
| timeout | 一行の実行基盤停止上限 | s | 2; harness protection, not measured latency | positive scalar |
| payload_sha256 | 固定記述結果の内容識別子 | not physical | SHA256 of fixed fixture bytes | hex string |
| done / cancelled | 保持したTaskの終了・取消し状態 | 1 | actual Task introspection | exact bool |
