# Regular-file admission for a bounded passive reader

**Result: PASS_REGULAR_FILE_ADMISSION_BOUNDARY_SCOPED.**
Issue #3947, successor to #3876. This directory contains a completed, research-only
input-admission experiment, not a production reader or a runtime change.

The exact existing reader's byte bound did not prevent a finite no-response
outcome on the two FIFO fixtures. A separate one-open regular-file adapter
refused those inputs while preserving the declared regular-file receipts.
A byte bound is not an execution-time guarantee.

## Provenance and allocation

| Item | Identity |
| --- | --- |
| Allocation | `input-kind-c82e-20260922-01` |
| Initial main | `b2457b746a6df06f6536585dfe2ab937aff639f4` |
| Source-first freeze commit | `fdad932e745dec1f8e5647348303812bf3469bfe` |
| Upstream reader Git blob | `ea72c166c2cea511ea91031dfbb14563fe4e3245` |
| Formal invocations / replacements | 1 / 0 |
| Formal cases / excluded construction cases | 42 / 14 |
| Formal raw SHA-256 | `b9e512737490b97097442bb1aec40f51dacb16c25358f6c2720a110090cdae34` |
| Formal raw size | 89,269 bytes |
| Freeze manifest SHA-256 | `80542efc6ad812fc53104628abda03780648651d0b02af83d3eaea7d6b435aef` |

The freeze commit and Issue comment preceded the only formal invocation.
`FORMAL_INVOCATION.json` records the exclusive source gate. All frozen source
hashes matched before and after the experiment. The actual environment was the
provided Linux x86_64 execution container, CPython 3.13.5, standard library only.
Docker was unavailable; this is not a Docker Desktop or OrbStack replication.

## H / T / D / C / U

**H:** limiting bytes does not bound blocking FIFO open/read. A one-open,
nonblocking-descriptor regular-file check plus bounded snapshot should reject
non-regular inputs and preserve the exact reader's regular-file semantics.

**T:** two policies, seven input cases, three repetitions, alternating arm order:
42 fresh exec'd reader processes. Fixed 512-byte read bound, 32-record bound,
three deterministic DeliveryLedger-format records. The external one-second
response deadline starts after child readiness and the supervisor's GO. A separate
writer in the live-writer FIFO fixture is attached before GO and emits no FIFO
bytes. Its temporary attachment anchor is closed before measurement. No historical
corpus, actual event producer, model, GUI or input action is used.

**D:** all frozen cases must reconcile with raw bytes, cursor prefix reconstruction,
source/process identities, timing order and cleanup. The exact reader must show
six FIFO no-response outcomes; the adapter must refuse all nine non-regular
inputs without timeout; regular receipts and overflow behavior must match.
The separately executed raw-only auditor returned zero errors. Its implementation
imports neither the runner nor the upstream reader, but was authored by the same
agent; this is not independent human review.

**C:** trusted, private local inputs and one declared lifetime. Symlinks to regular
files are intentionally allowed after validating the descriptor actually opened.
The control and adapter use the same unchanged upstream reader and notifications.
The adapter adds a bounded copy and temporary file; no speedup is claimed.

**U:** no hard deadline for arbitrary storage, remote filesystems or device opens;
no hostile-source authenticity, power-loss durability, producer epochs, concurrent
cursor commits, host crash persistence, ACK, model consumption, useful-feedback
latency, GUI/task success, or production promotion. Finite no-response observations
are not proof of permanent deadlock. A successful hypothesis test does not declare
the baseline safe for non-regular inputs.

## First-outcome results

Each cell contains three cases.

| Input | Exact reader | Regular-snapshot adapter |
| --- | --- | --- |
| Complete regular JSONL | 3 exact three-record receipts | 3 identical receipts |
| Incomplete last record | 3 exact two-record/incomplete-tail receipts | 3 identical receipts |
| Over 512-byte bound | 3 `STREAM_READ_BOUND_EXCEEDED` | 3 same rejections |
| Symlink to regular file | 3 exact three-record receipts | 3 identical receipts |
| Directory | 3 `IsADirectoryError` | 3 `NON_REGULAR_INPUT` |
| FIFO, no writer | 3 no responses by the one-second deadline | 3 `NON_REGULAR_INPUT` |
| FIFO, attached writer with no bytes | 3 no responses by the one-second deadline | 3 `NON_REGULAR_INPUT` |

All six timed-out children were observed alive at the deadline, terminated with
SIGTERM and reaped. All other readers exited zero. All six owned writer processes
closed and exited zero. The auditor reconciled all 42 reader cleanups, writer
identities and zero-write protocol, unchanged inputs and every exposed receipt's
`authority=none`, `acknowledged=false`, `input_dispatched=false`. Zero FIFO writes
are supported by frozen writer source and protocol, not an independent syscall
trace. Driver exit: 0. Auditor exit: 0. Auditor errors: 0.

Formal driver wall duration was 80.363035615 seconds including process startup.
This is descriptive, not a performance comparison or a reliability bound.

## Retained failures and transport history

The one excluded construction block completed 14 cases, but its encompassing
20-second tool command timed out. The recovered driver's recorded duration was
27.782796835 seconds. The first bundled test command's exit was not recovered;
its empty logs are retained and not called a successful test. A separate test-only
invocation on that same construction raw exited zero: nine tests, including eight
rejected evidence corruptions. No construction case is pooled with formal results.

During formal execution the PTY polling handle became unavailable. Read-only
process/file checks found the original driver still running; it was not relaunched.
Its original outputs subsequently completed with exit zero.

Three manually transmitted blob payloads failed Git-object identity comparison:
one whole-gzip attempt and two chunk attempts. All three were rejected before any
tree or branch reference; their IDs and expected IDs are retained in
`EVIDENCE_MANIFEST.json`. Exact local chunks were transmitted again and every
accepted returned Git blob ID matched the local object hash. This repaired evidence
transport, not the experiment. No raw rows or measurements were regenerated.

## Audit the retained evidence without rerunning the experiment

Eight binary chunks under `evidence/` losslessly retain both raw JSON files.
The manifest binds part sizes, Git object IDs, SHA-256 digests, concatenated gzip
and decompressed raw bytes. `restore_evidence.py` is a post-result publication
helper, not frozen measurement code. It validates all bytes before writing to a
fresh directory and never executes the experimental program.

From this directory, with a new output path:

```sh
python -B restore_evidence.py /tmp/issue3947-evidence-new
python -B audit.py /tmp/issue3947-evidence-new/formal-01/RAW.json FREEZE.json
python -B test_audit.py /tmp/issue3947-evidence-new/construction-01/RAW.json
```

The publication restoration smoke check reproduced both raw hashes and the same
zero-error formal audit. The same nine construction evidence tests passed again.
These are read-only rechecks, not new scientific allocations. Exact original and
restoration stdout/stderr/exit receipts are in `RETAINED_RECEIPTS.json`.

**Do not run `launch.py` or repeat the consumed allocation.** Its retained invocation
marker intentionally makes a normal second invocation fail closed. Any materially
new experiment needs a distinct Issue, allocation, path and pre-outcome freeze.
`PLAN.md` is the immutable preregistration; `AUDIT.json` the original formal audit;
`COMMANDS.json` the operation summary. The raw JSON contains every source input
byte, request, received protocol line, process exit and case identity needed for
this auditor; recreating FIFOs or obtaining the old absolute paths is unnecessary.

## Integration handoff and remaining roadmap

Readiness: this bounded experiment is complete. Own scope is additive only under
`research/integration/passive_reader_input_kind_c82e_v1/`, branch
`research/passive-reader-input-kind-c82e-v1`. Source recovery, excluded construction,
freeze, first formal block, raw-only audit, mutation tests and lossless retention
are complete. PR/main integration is recorded on #3947, not assumed by this file.

The integration implication is a regular-local-file admission requirement for a
host using this research reader. Do not silently expose the adapter in production
or claim general I/O cancellation. Before promotion, #3876 still needs an actual
production producer/host boundary, ordered model-visible presentation and the
separate lifecycle/retention/ACK contracts. Do not add a synthetic queue or sensor
merely to satisfy that gate.

Preserve #493/PR #479's already-performed allocation, closed #462, and active
#2547/#3934. Parallel #3931 owns crash persistence, #3933/#3937/#3938 lifecycle
binding, and #3941 concurrent cursor commits; this result neither reruns nor closes
them. Other workers' branches and all old evidence remain untouched. The broad
repository ROADMAP and parent #3876 remain open. Age or main ancestry alone does
not authorize deleting another worker's branch.
