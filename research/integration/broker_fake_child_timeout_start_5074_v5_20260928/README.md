# Issue #5074 — running-child timeout boundary

This study is a fresh successor to #5036's preserved `HOLD_EVIDENCE_INCOMPLETE`.
It does not alter #5036, #5013, or any earlier raw allocation. The question is
whether the unchanged local broker's timeout result is observed after the fake
child is demonstrably running, rather than before process startup.

## H / T / D / C / U

**H.** With the current-main broker frozen at Git blob
`5734f54f318db9ac5e96b2bed6f6bed105ac39ff`, child exits 0 and 23 propagate
exactly; a child that has durably logged its invocation and emitted a
host-visible start marker before the broker deadline produces the
typed `HOST_BROKER_SUBPROCESS_TIMEOUT` receipt and empty response; missing
executable is typed non-success; malformed JSON does not invoke a child; idle
`--once` is externally bounded with no IPC result; and queued requests process
only lexical-first `a`. All authority receipts remain false.

**T.** One new allocation: `broker-fake-child-timeout-start-20260928-01`.
Branch: `research/broker-fake-child-timeout-start-5074-v5-20260928`; additive path:
`research/integration/broker_fake_child_timeout_start_5074_v5_20260928/`. Local Docker
Desktop only, linux/amd64, cached image ID
`sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`.
One formal container invocation runs seven isolated cases; one separate
container invocation runs the frozen independent auditor. Before formal,
construction tests, source/image/path gates, tmpfs executable probe, sibling
resource ownership, and three absent evidence destinations (formal output,
audit output, invocation receipt) must pass. Exact
realized command and absolute mount paths are written to a host-side receipt
before launching Docker. The timeout parent must observe and timestamp the
child's fsynced invocation record and start marker within three seconds. The
raw child and broker monotonic timestamps must prove the child and parent
marker observation precede `broker.started_ns + timeout_s`; the row timeout,
broker-receipt timeout and frozen value (5 s) must match. The broker,
child-start record, and parent marker observation all use the same
`time.perf_counter_ns()` clock inside the pinned Linux container. No retries
or pooling.

**D.** PASS only if all seven frozen outcomes reconcile, the timeout row proves
the child started before the deadline, all authority flags are false, the raw
audit has zero errors, and 17/17 frozen corruption controls reject, including
semantic-table/file-byte divergence. A complete
contradiction is scoped FAIL. Missing start marker, command receipt, hashes,
resource ownership, or audit is HOLD/STOP, never scientific FAIL/PASS.

**C.** No broker source modification; network none; read-only root and source;
fresh output-only writable mount; 0.25 CPU, 256 MiB, 32 PIDs, dropped caps,
no-new-privileges, bounded executable tmpfs. No real Codex executable,
credentials, provider/model, GPU, GUI, OS input, or application effect.

**U.** One Windows PC, one Docker Desktop linux/amd64 Python image and seven
deterministic fake-child cases. No OrbStack equivalence, provider/model
semantics, task correctness, GUI authority, latency, or product claim.

Formal, audit, and receipt outputs are isolated under this study directory as
`formal-output/`, `audit-output/`, and `invocation-receipt.json`; they do
not occupy a shared parent-level `research/integration/` destination.

## One-shot protocol

1. Verify current main `8c6019147dcf91054f2d63bcd872f8a96ae2434f` and exact broker blob; check issue/branch/path collisions.
2. Run only construction checks. They never import or invoke the broker.
3. Confirm explicit shared Docker slot ownership and fresh inventory in the
   `desktop-linux` context. Never
   stop or modify pre-existing containers.
4. Verify formal output, audit output, and receipt paths are absent. Persist exact command/mount receipt,
   including resolved host paths, image ID/platform, source IDs/hashes, and
   allocation ID.
5. Run the seven-case formal runner in one container exactly once. Each case
   uses fresh private IPC. The timeout child fsyncs its call log, writes its
   start marker, then sleeps 8 s against a 5 s broker timeout. Parent waits up
   to 3 s for both records; missing marker is a typed STOP. Independent audit
   reconciles row tables to hashed child-call, receipt and response bytes.
6. Run `audit.py` in one distinct fresh restricted container against raw output;
   it must reject all seventeen frozen evidence mutations (15 semantic in-memory controls plus two raw-file controls).
7. Publish raw output, hashes, dispositions and limitations through a reviewable
   additive PR. Keep all historical branches and results intact.

## Formal case matrix

`exit-0`, `exit-23`, `timeout-after-start`, `missing-executable`,
`malformed-json`, `idle-once`, and `sorted-once`. `--once` is always passed.
The host invocation receipt is outside the formal output mount and is mounted
read-only inside the container; the runner copies it into raw evidence.

## Preserved predecessor construction records

The v2 lane's local marker synchronization unittest passed 1/1. A disposable
container on the pinned image created/chmodded/executed a tmpfs child, observed
its start marker, then killed it for cleanup (`CONSTRUCTION_MARKER_PASS -9`).
The later v2 isolated test-suite command exited 1 because its read-only
container had no writable temporary directory and one test imported a
workspace-root-only package. This is a construction STOP, not a broker result;
the complete output is retained in the #5074 Issue thread. No broker was
mounted or invoked and formal case count remains zero. v4 independently fixes
the isolated import and provides bounded `/tmp`; it must pass the pinned-image
construction suite before the formal allocation is considered ready.

The first v4 local Docker construction suite passed 12/12 with the pinned image,
read-only source/root, network disabled, 0.25 CPU, 256 MiB, 32 PIDs, and a
bounded writable `/tmp`. That run predated a final source hardening change that
unified the broker, child, and parent timestamp API on `perf_counter_ns()` and
added a frozen-source-hash regression. Its result is retained as a successful
intermediate construction rung, not as validation of the final source freeze;
the final suite must be rerun in local Docker before formal launch.
