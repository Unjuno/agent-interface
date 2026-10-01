# Issue #5846 — successor T0 protocol freeze (pre-formal)

This is a new, additive successor experiment to the immutable Issue #5795
allocation record. The predecessor's `STOP_FORMAL_ARGV_MISMATCH` consumed its
one-shot allocation with candidate/auditor counts 0/0; it is not retried or
reclassified here. Issue #5846 is the successor request. The package is on
branch `research/crash-atomic-suppression-5846-t0-20261001-02`, under
`research/experiments/crash_atomic_suppression_5789_t0_successor_5846_02/`.
Allocation-01 stopped before candidate when main advanced at its start gate;
its immutable STOP is in the preceding package path and on PR #5896. This is
a distinct allocation-02 package. Preparation starts from main
`0707d2254b2789c0bbab97d65645772c8da76a9f`; freeze current main again inside
the reserved window and pin the actual source commit and hashes in
`FREEZE.json` before any guest/container call. This successor preserves the protocol and corrects host/guest
path mapping; that mapping has construction tests only and is not formal
evidence.

## H/T/D/C/U

**H.** A transactionally persisted suppression binds candidate identity,
authority generation, and disposition so an acknowledged suppression cannot be
lost and an old-generation proposal cannot regain admission across supported
process-kill/restart boundaries. A pre-commit interruption may recover the
previous committed state, but recovery must be UNKNOWN/fail-closed until
reconciled. A post-commit/pre-ack interruption is not an acknowledged commit;
it must not be reported as one.

**T.** Three toy policies in separate child processes: A, memory-only; B,
separate candidate and generation writes; C, one SQLite transaction. A parent
runner owns the child and sends SIGKILL at frozen observable barriers. Cases
cover pre-write, after first split write, pre-commit, post-commit/pre-ack,
acknowledged commit/restart, same fingerprint/new generation, changed target
under same label, reactivation, frozen-clock TTL expiry at an exact boundary,
pre/post-expiry probes, transactional GC to a retained retirement tombstone,
malformed record, and repeated restart. This is logical fixture GC, not
physical database-file compaction. One container candidate writes JSONL to its
sole output mount. A separate raw-only auditor process/container reads retained
bytes read-only and does not import candidate modules. No GUI, model, network,
external receiver, shared runtime, multi-writer, or power-loss semantics.

Expiry/GC schedule row: suppression is created at fixture time 100 with TTL 50
(`expires_at=150`); probe at 149 must deny as unexpired; GC at 149 must perform
zero transitions and preserve the live row; probe at 150 must fail closed while
expired state awaits GC; transactional GC at 150 must change exactly one row to
`RETIRED` with `retired_at=150`; the row must still exist; probe at 150 after GC
must deny through the retained tombstone. The independent auditor checks every
clock, row count, retained field, and disposition. No wall-clock sleeps occur.

**D.** PASS is restricted to the frozen process-crash schedule: all
acknowledged commits survive restart, no stale-generation admission occurs,
expired identities fail closed before GC and remain denied by a retained
tombstone after logical GC, retired identities cannot regain authority, and
pre-commit or post-commit/pre-ack states remain UNKNOWN until positively
reconciled. A stale admission or lost acknowledged record is FAIL. Incomplete
provenance, corrupt input, ambiguous process outcome, absent rows/exits, or
audit disagreement is STOP/HOLD. No retry or post-result gate changes.

**C.** Compare with monotone generation-bound rejection and durable idempotency;
durable anergy may be unnecessary state. A/B are diagnostic baselines, not
claims that an interface implementation uses those policies.

**U.** `SIGKILL` tests process termination only, not power loss, storage-device
cache loss, filesystem guarantees, concurrent serialization, identity collision
resistance, GUI behavior, or product safety.

## Allocation start gate

The directly user-authorized fresh allocation-02 slot is recorded in
coordination Issue #5085 as `crash-atomic-suppression-5846-t0-20261001-02`,
12:30–13:10 UTC. It requires a new isolated ARM64 Ubuntu 24.04 OrbStack guest
`crash-atomic-5846-20261001-02`, 1 vCPU, 2 GiB memory, 16 GiB disk, and a
guest-local Docker context `crash-atomic-5846-local-02` whose endpoint is
`unix:///var/run/docker.sock`. At 12:30 UTC, re-fetch main, Issues/PRs/branches
and coordination queue; confirm no overlapping active guest, unique guest and
context, pinned image identity, host/guest path mapping, source/freeze hashes,
empty separate outputs, and resource limits. The registry index digest is
`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`;
the Linux/ARM64 platform manifest digest is
`sha256:950206c37262dd86c55659797f6ee418fee30535072f65a82ed470d985f5cda5`,
and its image-config digest is
`sha256:8630ab77c5adf06e1f914483db4dd70e3fa59118160daab9b0ee75e685344221`.
These are not interchangeable with the guest daemon's `image inspect .Id`;
that exact runtime value is captured and verified before candidate launch.
The candidate itself uses Docker `--network none`, read-only
root/source, one CPU, 256 MiB, 64 PIDs, bounded tmpfs and output mounts. Any
failed or ambiguous gate is retained as STOP with candidate/auditor counts 0/0;
do not invoke candidate or retry. If the candidate exits zero, run the separate
auditor once. Stop this guest by 13:10 UTC and preserve its evidence.

Formal outputs are distinct from all host construction checks. Within the
reserved window, provision the named guest, create its guest-local Docker
context for `unix:///var/run/docker.sock`, and verify that context from inside
the guest. Pull the exact image ref with `--platform linux/arm64`, then inspect
it through that context. Confirm `.Id`, `Os`, `Architecture`, and `RepoDigests`.
Run `finalize_freeze.py` with the observed `.Id`, source commit, context,
endpoint, and mounted host source root; it writes final source/launcher/audit/
schedule hashes, the guest-argv→host-output mapping, and refreshed
`SHA256SUMS`. Rerun local CI and checksum validation before candidate launch.
The formal launcher independently rechecks the frozen `.Id` and platform.
Do not change this protocol after the first formal candidate invocation.
