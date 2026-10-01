# Issue #5795 — T0 protocol freeze (pre-construction)

Parent idea: GitHub Issue #5789. Allocation request: Issue #5795. Intake main
before construction: `ff2164a8b16d386571c91ebba19f6604b4776581`. The branch was
subsequently rebased, before formal execution, onto newer main
`b7b724ee06125a146c68071c1d03e9556a70c5f6`.

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
under same label, reactivation, expiry/GC, malformed record, and repeated
restart. One container candidate writes JSONL to its sole output mount. A
separate raw-only auditor process/container reads retained bytes read-only and
does not import candidate modules. No GUI, model, network, external receiver,
shared runtime, multi-writer, or power-loss semantics.

**D.** PASS is restricted to the frozen process-crash schedule: all
acknowledged commits survive restart, no stale-generation admission occurs,
expired/retired identities cannot regain authority, and pre-commit or
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

This is a protocol/construction freeze, not authorization to start a Docker,
OrbStack, or Obstac-managed guest. Run no formal candidate until Issue #5795 is
explicitly assigned a non-overlapping isolated guest/daemon slot, endpoint and
owner by the resource coordinator. Existing repository Obstac launchers use a
shared OrbStack Docker context and are not reused as an isolation grant. At the
formal start gate, refetch main, Issues/PRs/branches/queue, verify the exact
guest-local Docker endpoint, pinned image identity, source/freeze digests,
fresh empty mounts, and all process/output limits. Any failed or ambiguous gate
is retained as STOP with candidate/auditor counts 0/0.

Construction outputs and tests are excluded from formal denominators. Do not
change this protocol after the first formal candidate invocation.
