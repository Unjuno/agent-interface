# Issue #5074 — running-child timeout boundary

This study is a fresh successor to #5036's preserved `HOLD_EVIDENCE_INCOMPLETE`.
It does not alter #5036, #5013, or any earlier raw allocation. The question is
whether the unchanged local broker's timeout result is observed after the fake
child is demonstrably running, rather than before process startup.

## H / T / D / C / U

**H.** With the current-main broker frozen at Git blob
`5734f54f318db9ac5e96b2bed6f6bed105ac39ff`, child exits 0 and 23 propagate
exactly; a child that has durably logged its invocation and emitted a
host-visible start marker before the parent arms the timeout produces the
typed `HOST_BROKER_SUBPROCESS_TIMEOUT` receipt and empty response; missing
executable is typed non-success; malformed JSON does not invoke a child; idle
`--once` is externally bounded with no IPC result; and queued requests process
only lexical-first `a`. All authority receipts remain false.

**T.** One new allocation: `broker-fake-child-timeout-start-20260928-01`.
Branch: `research/broker-fake-child-timeout-start-5074-v2`; additive path:
`research/integration/broker_fake_child_timeout_start_5074_v1/`. Local Docker
Desktop only, linux/amd64, cached image ID
`sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`.
One formal container invocation runs seven isolated cases; one separate
container invocation runs the frozen independent auditor. Before formal,
construction tests, source/image/path gates, tmpfs executable probe, sibling
resource ownership, and an empty fresh output directory must pass. Exact
realized command and absolute mount paths are written to a host-side receipt
before launching Docker. The timeout parent must observe and timestamp the
child's fsynced invocation record and start marker before timeout is permitted
to elapse. No retries or pooling.

**D.** PASS only if all seven frozen outcomes reconcile, the timeout row proves
the child started before the deadline, all authority flags are false, the raw
audit has zero errors, and 8/8 fixed corruption controls reject. A complete
contradiction is scoped FAIL. Missing start marker, command receipt, hashes,
resource ownership, or audit is HOLD/STOP, never scientific FAIL/PASS.

**C.** No broker source modification; network none; read-only root and source;
fresh output-only writable mount; 0.25 CPU, 256 MiB, 32 PIDs, dropped caps,
no-new-privileges, bounded executable tmpfs. No real Codex executable,
credentials, provider/model, GPU, GUI, OS input, or application effect.

**U.** One Windows PC, one Docker Desktop linux/amd64 Python image and seven
deterministic fake-child cases. No OrbStack equivalence, provider/model
semantics, task correctness, GUI authority, latency, or product claim.

## One-shot protocol

1. Verify latest main and exact broker blob; check issue/branch/path collisions.
2. Run only construction checks. They never import or invoke the broker.
3. Confirm explicit shared Docker slot ownership and fresh inventory. Never
   stop or modify pre-existing containers.
4. Verify fresh output path is absent. Persist exact command/mount receipt,
   including resolved host paths, image ID/platform, source IDs/hashes, and
   allocation ID.
5. Run the seven-case formal runner in one container exactly once. Each case
   uses fresh private IPC. The timeout child fsyncs its call log, writes its
   start marker, then sleeps 5 s against a 2 s broker timeout. Parent waits up
   to 3 s for both records before the timeout interval starts; missing marker
   is a typed pre-formal/measurement STOP and cannot be silently retried.
6. Run `audit.py` in one distinct fresh restricted container against raw output;
   it must reject all eight frozen evidence mutations.
7. Publish raw output, hashes, dispositions and limitations through a reviewable
   additive PR. Keep all historical branches and results intact.

## Formal case matrix

`exit-0`, `exit-23`, `timeout-after-start`, `missing-executable`,
`malformed-json`, `idle-once`, and `sorted-once`. `--once` is always passed.
The host invocation receipt is outside the formal output mount and is mounted
read-only inside the container; the runner copies it into raw evidence.

## Construction status

The local marker synchronization unittest passed 1/1. A disposable container
on the pinned image created/chmodded/executed a tmpfs child, observed its start
marker, then killed it for cleanup (`CONSTRUCTION_MARKER_PASS -9`). No broker
was mounted or invoked; formal case count remains zero. The #5066 sibling lane
has a first-use priority after this brief probe; this allocation must wait for
its explicit completion/release before any further Docker invocation.
