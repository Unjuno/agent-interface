# Authorization time is not recoverable from the current lifecycle state

**PASS_ORDER_MEMORY_SCOPED.** This new ordinary construction retains 108 typed
synthetic cases and a two-history witness. It compares current main with a
simple floor from an existing observation timestamp and with an isolated
candidate that remembers successfully accepted authorization time. No shared
runtime code, workflow, old allocation or historical disposition is changed.

| Arm | Complete rows | Accepted begin calls | Accepted before authorization |
|---|---:|---:|---:|
| current kernel | 36 | 16 | 11 |
| existing observation floor | 36 | 12 | 7 |
| remembered authorization floor | 36 | 5 | 0 |

All requests/times are authored fixtures. These counts do not describe native
input, physical time, failure frequency or task benefit. The candidate enforces
a chosen same-clock API chronology rule; the current v1 schema has no valid-from
lease field, so this is not proof that every before-registration timestamp
describes use outside the original lease's actual authority interval.

## What changes the integration decision

Two successful authorization histories use the same immutable observation,
binding and lease. One accepts authorize(now=200), the other authorize(now=400).
In the current kernel their complete before-begin fields are equal. The same
request with begin(now=300) is accepted in both. An observation floor at 100 also
leaves equal fields and accepts both histories. It improves some cases but
cannot recover the forgotten grant time. The memory candidate differs only in
its stored authorized_ns and accepts the earlier-grant history only.

A deterministic checker given equal state and equal next input cannot choose
different decisions for those histories. If the API must enforce ordering of
caller-supplied authorization/begin times, it therefore needs distinguishing
history information, a supplied valid-from bound, or a stronger caller contract.
The four-line memory change is one implementation; this does not prove that an
integer field is the uniquely minimal memory encoding or the fastest solution.

A trustworthy sequential monotonic-clock caller is a simpler no-added-state
alternative: genuine readings already respect call order. This construction
does not show a failure of that alternative, synchronize different clocks, or
justify automatically promoting another runtime field. Native clock provenance
and caller requirements need to be decided before source adoption. The snapshot
floor uses the same synthetic clock; its extra capture-clock assumption is
explicit rather than treated as evidence from real backends.

The memory candidate stores a grant only after successful authorize checks and
checks it after strict begin-time typing but before any begin state mutation.
It preserves duplicate begin, request/authority mismatch, receipt-start, release
and begun-cancellation guards already adopted on source main. Keeping grant
memory separate from execution_started_ns preserves the existing cancellation
semantics when no execution has begun. Equality stays representable; completion
and release after lease expiry remain representable. No end cutoff is added.

## Actual validation and preserved first results

- Original source is main `2c0c1183b861519fde7c71462a589fb904c3451e`; nine exact
  Git kernel source/test blobs are in source/*.py.txt. Source/base identities,
  environment and the prospective plan are in BEFORE_BASELINE.json.
- New baseline eight-method check first exited1 with five expected missing
  ContractError assertions. Full original/private and public redacted streams
  are identified by its receipt. This failure was not replaced with a pass.
- FINAL_FREEZE.json fixed the two candidate files, producer, auditor, test and
  108-case denominator at 04:43:00.084771 UTC, before the sole matrix child
  ran at 04:44:35.652934–04:44:35.807483 UTC. Source was reread after checks.
- Memory-candidate boundaries:8/8 normal and8/8 -O. The candidate composed with
  the original nine-source kernel copy:43/43 normal and43/43 -O. The two groups
  are separate children with their actual commands, source hashes, UTC, PID,
  exit and stream hashes; do not mistake a wrapper's expected exit for the child.
- Independent raw-only audit reconstructs108 unique ordered rows and every
  complete before/after field, checks all refusal/request identity evidence and
  the history witnesses. Errors=[];12/12 effective copied-data corruptions
  refuse. It imports neither producer nor kernel. Raw was not regenerated to
  obtain the audit result.
- Prior original-baseline43 normal/-O results are reused only after byte-level
  equality of all nine source/test files and the same Python3.11.9 stdlib scope.
  Their original source context, child receipts and complete streams are in
  prior-validation/. They are separately attributed and not a new baseline run.

The original registry tests call inert FakeBackend metadata stubs. No native
backend, platform input, GUI, model, container, WSLc, GPU or shared resource was
used. The environment is Windows10.0.26300, AMD64 CPython3.11.9, stdlib only.
No performance trial, formal allocation or extra worker was used. Synthetic
nanoseconds encode relationships, not measured nanosecond accuracy.

## Retention and read-only review

matrix.raw.json is the complete first producer stdout, not an aggregate.
AUDIT.json is the exact first auditor stdout. logs/ retains every child receipt
and both public streams. Only owned absolute path prefixes in public traceback
text are replaced; original stream hashes and private original/actual-argv
retention are disclosed. Raw has no private path and is exact unchanged.
SHA256SUMS covers every delivered member except itself. Final ordinary author
wrapper versions are retained as .py.txt under author-wrappers/; the invoker
added one audit-only profile after the candidate boundary checks. It did not
change the frozen producer, auditor or test definitions. Wrappers originally
ran from the private work root and must not be executed from their archival
location. No producer/auditor source change, setup failure or hidden retry
occurred in the 108-row matrix. PUBLICATION_FAILURES.json separately preserves
the first ordinary staging refusal because this new path lay outside the own
clone's sparse-checkout cone; staging is repaired without any matrix rerun.

Read-only audit from this directory:

```text
python -B audit_retained.py matrix.raw.json
```

The ordinary tests can be repeated into new output if needed for a concrete
source/environment change, using AUTHORITY_ORDER_ARM=authorization_floor and
check_boundaries.py. Reviewers can reuse retained tests after validating their
actual source/test/environment applicability; do not rerun a matrix merely to
repair delivery, bookkeeping or a data reader. All copied runtime is .txt and
the helpers are explicit guarded entrypoints, with no test_*.py/default workflow
selection. This archive is not a promoted runtime or a future-main approval.

The notation, units, fixture domains and original H/T/D/C/U gates remain in
PLAN.md. #5215 stays open; #5216/#5225/#5229 and their HOLD interpretations are
untouched. #6875 types, #6894 cancellation uncertainty and #6908 compiled capture
timing remain separate work. The broader computer-control goal remains open.
