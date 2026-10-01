# Issue #5795 — T0 protocol freeze (pre-formal)

Parent idea: GitHub Issue #5789. Allocation request: Issue #5795. Intake main
before construction: `ff2164a8b16d386571c91ebba19f6604b4776581`. After host
construction, the branch was rebased onto current main
`49db21e330768800e8b3486203b70306f4e402f6`. The executable manifest is
`FREEZE.json`; it pins source commit
`6aa357d1b27c44b591b9d640b5ef440d007bb3e5` and the dedicated guest-local
Docker endpoint. Construction code remains in this additive package but is
not counted as formal evidence.

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
malformed record, and repeated restart. This is logical fixture GC, not physical
database-file compaction. One container candidate writes JSONL to its sole output mount. A
separate raw-only auditor process/container reads retained bytes read-only and
does not import candidate modules. No GUI, model, network, external receiver,
shared runtime, multi-writer, or power-loss semantics.

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
tombstone after logical GC, retired identities cannot regain authority, and pre-commit or
post-commit/pre-ack states remain UNKNOWN until positively reconciled. A stale
admission or lost acknowledged record is FAIL. Incomplete provenance, corrupt
input, ambiguous process outcome, absent rows/exits, or audit disagreement is
STOP/HOLD. No retry or post-result gate changes.

**C.** Compare with monotone generation-bound rejection and durable idempotency;
durable anergy may be unnecessary state. A/B are diagnostic baselines, not
claims that an interface implementation uses those policies.

**U.** `SIGKILL` tests process termination only, not power loss, storage-device
cache loss, filesystem guarantees, concurrent serialization, identity collision
resistance, GUI behavior, or product safety.

## Allocation gate

An explicit user-authorized, non-overlapping allocation is recorded in the
coordination issue: `crash-atomic-suppression-5795-t0-20261001-01`,
06:00–06:20 UTC, one new ARM64 Ubuntu 24.04 OrbStack guest
(`crash-atomic-5795-20261001`), 1 vCPU, 2 GiB memory, 16 GiB disk, isolated
from host and peer networking. The daemon and named Docker context live inside
that guest; the endpoint is `unix:///var/run/docker.sock`. The candidate itself
additionally uses Docker `--network none`, read-only root/source, one CPU,
256 MiB, 64 PIDs, and bounded tmpfs/output mounts. The fixed image was pulled
and inspected in this guest as
`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
`linux/arm64`. At the formal start gate, refetch main,
Issues/PRs/branches/queue, verify endpoint, image identity, source/freeze
digests, fresh empty mounts, and limits. Any failed or ambiguous gate is
retained as STOP with candidate/auditor counts 0/0.

Construction outputs and tests are excluded from formal denominators. Do not
change this protocol after the first formal candidate invocation.
