# Issue #5846 — successor T0 protocol freeze (pre-formal)

This is a new, additive successor experiment to the immutable Issue #5795
allocation record. The predecessor's `STOP_FORMAL_ARGV_MISMATCH` consumed its
one-shot allocation with candidate/auditor counts 0/0; it is not retried or
reclassified here. Issue #5846 is the successor request. The package is on
branch `research/crash-atomic-suppression-5846-t0-20261001`, under
`research/experiments/crash_atomic_suppression_5789_t0_successor_5846/`.
Preparation is based on main `8f18bb65d75deaaafed8b4e6ebbd430371c1d05`;
the final source commit and manifest hashes are bound in `FREEZE.json` before
the start gate. This successor preserves the protocol and corrects host/guest
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

The directly user-authorized successor slot is recorded in coordination Issue
#5085 as `crash-atomic-suppression-5846-t0-20261001-01`, 07:35–08:05 UTC. It
requires a new isolated ARM64 Ubuntu 24.04 OrbStack guest
`crash-atomic-5846-20261001`, 1 vCPU, 2 GiB memory, 16 GiB disk, and a guest-local
Docker context `crash-atomic-5846-local` whose endpoint is
`unix:///var/run/docker.sock`. At 07:35 UTC, re-fetch main, Issues/PRs/branches
and coordination queue; confirm no overlapping active guest, unique guest and
context, pinned image identity, host/guest path mapping, source/freeze hashes,
empty separate outputs, and resource limits. The image is pinned as
`python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`
(`linux/arm64`). The candidate itself uses Docker `--network none`, read-only
root/source, one CPU, 256 MiB, 64 PIDs, bounded tmpfs and output mounts. Any
failed or ambiguous gate is retained as STOP with candidate/auditor counts 0/0;
do not invoke candidate or retry. If the candidate exits zero, run the separate
auditor once. Stop this guest by 08:05 UTC and preserve its evidence.

Formal outputs are distinct from all host construction checks. The exact
guest-side launcher argv, host-side output mapping, assigned runtime, source
commit and hashes are pinned in `FREEZE.json`. Do not change this protocol after
the first formal candidate invocation.
