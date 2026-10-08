# Issue #6331 — wake-fenced lease validity T0

## H / T / D / C / U

**H.** Given the exact current runtime `Lease` implementation and a frozen finite clock/owner trace, a long suspend gap can leave its injected `perf_counter_ns` relative lease apparently live on first post-wake check even though a wall/suspend-inclusive horizon exceeds the original TTL. A BOOTTIME-based absolute deadline rejects after the long gap. A wake-generation fence blocks old authority, requests held-input release, and requires release acknowledgement plus fresh binding before a new bounded lease; missing/late wake evidence returns `UNKNOWN_WAKE_COVERAGE`.

**T0.** No machine sleep, GUI, physical input, or model. Execute the exact current `research/live_control/lease.py` in a pinned isolated Docker container with synthetic monotonic/boottime readings. Eight frozen scenarios cover no gap, short wake, long wake, awake expiry, missing/late wake notice, held input without release acknowledgement, acknowledged release plus fresh rebind, and incomplete wake/clock coverage. Compare the exact current Lease using injected relative clock, a suspend-inclusive absolute deadline, and a small wake-fence state machine. Candidate emits raw rows. An independent raw-only auditor uses separate source/property logic to reconstruct every row and classify authority, release request/receipt and first post-wake action.

## D

`PASS_METHOD_SCOPED` only if all frozen rows reconcile; no-gap and short-gap controls retain the exact current Lease's inclusive/exclusive boundary; the long-gap trace distinguishes relative-live from BOOTTIME-expired; a wake fence blocks the old generation; missing/late wake evidence is `UNKNOWN_WAKE_COVERAGE`; a held input produces a release request but **no claim of release** without an independent ack; post-release fresh rebind creates only a new TTL; and all corruption controls fail closed. A mismatch is FAIL/HOLD, not tuned away. Construction checks are separate.

## C / U

Current leases may already be scoped to process uptime rather than wall elapsed time; any existing runtime wake hook may make a redundant fence unnecessary. An awake delay is not OS suspend. Linux man-pages describe MONOTONIC vs BOOTTIME but do not prove OrbStack/WSLc host-wake mapping. T0 cannot prove real wake signal delivery, live held-input release, GUI revalidation, task effect, or production safety. No physical key/button is held or sent.

## Allocation and stopping

Allocation: `WAKE-FENCE-6331-T0-20261002-01`. Source base is frozen in `FREEZE.json`; additive branch/path only. Candidate once; auditor once only after candidate success; zero retries. Cached pinned `python:3.12-slim`, no pull, network none, read-only root/inputs, separate output, bounded resources. Preserve every raw outcome and command. Stop before invocation on source/main/image/path mismatch. Any actual suspend test requires a separate disposable VM/host authorization and is out of scope.
