# Issue 3996: empty tail is not stream finality

## Result and decision

**PASS_STREAM_FINALITY_BOUNDARY_SCOPED** for allocation
`finality-7f31-20260922-01`. This is a notification-stream contract result,
not task completion, ACK, model consumption, fresh action authority, or runtime
promotion. The unchanged existing reader behaved according to its contract;
the unsafe interpretation was the explicitly tested empty-end baseline.

One formal orchestration ran 12 cases (four scenarios, three repetitions),
with zero retries/replacements. Runner and separate raw-only auditor exited 0;
both stderr streams were empty. All eight frozen source digests remained exact.
The audit had no errors and rejected all 12 evidence-corruption controls.

In all 12 cases the exact reader returned an empty `end` tail while the actual
known producer remained alive behind the finish barrier. The baseline labelled
all 12 COMPLETE; the candidate labelled all 12 WAIT_PRODUCER. Nine later complete
notifications were actually delivered after the barrier. The three other second
records were retained as incomplete frames, not repaired or dropped.

| Terminal scenario | Cases | Producer exit | Candidate | Delivered records per case |
|---|---:|---:|---|---:|
| SEALED_COMPLETE | 3 | 0 | COMPLETE | 2 |
| ZERO_EXIT_UNSEALED | 3 | 0 | UNKNOWN | 2 |
| NONZERO_EXIT_SEALED | 3 | 7 | PRODUCER_FAILED | 2 |
| SEALED_PARTIAL | 3 | 0 | INCOMPLETE | 1 |

All 12 producers joined/reaped: nine exit 0 and three predeclared exit 7. There
were no unexpected exits or cleanup kills. All 48 reader calls retained neutral
authority/ACK/input fields. A failed producer does not erase the two already
received notifications. Unsealed zero-exit bytes are not asserted incorrect;
they lack the declared completeness attestation. Partial framing leaves the
cursor after record 1, despite a seal describing all written bytes.

## H / T / D / C / U

H: snapshot emptiness and producer termination are different facts. For one
trusted producer lifetime, a joined zero exit, its explicit final extent/sequence/
SHA256 receipt, and a fully drained matching exact cursor support the scoped
COMPLETE classification. No receipt/cursor comparison supplies task semantics.

T: public Issue #3996 preceded construction. Source commit
`079433154120c8743c6bc9d2f951d00e66b9d748` and freeze comment `5766724329`
preceded the sole formal invocation. Exact nine-file source-tree object
`feae517f1f5a51056d98b2dbf1e88caf966060de` matched a separately computed local
Git tree. Fixed scenario order and gates are in PLAN.md/FREEZE.json. The existing
DeliveryLedger generated the first/late records in actual exec'd processes; the
unchanged reader ran in the host. Pipe barriers selected order, not sleeps.

D: complete denominator/source/process/byte accounting; 12 live-idle baseline
false certifications but zero candidate certifications; late-record retention;
exact three-per-scenario terminal decisions; neutral authority; independent raw
reconstruction and corruption rejection. All declared gates passed. These are
directed cases, not estimates of a production failure probability.

C: the host owns the known producer and join result; there is exactly one writer,
none after join, and the retained file/seal is not externally mutated. SHA256 is
integrity, not authentication. Existing interactive_v17 does not thereby gain
this new fixture seal protocol. No production queue, sensor or action scheduler
was added. The classifier's success depends on those explicit ownership facts.

U: no producer restart, concurrent host commits, arbitrary partial pipe writers,
in-place file mutation, descriptor sharing, byte-capacity policy, crash-atomic
seal publication, power-loss durability, distributed exactly-once, model/GUI
benefit, timing improvement or production qualification. The source uses a
five-second ready select and communicate timeout with trusted complete ready
lines; it is not a general hard-deadline I/O implementation. Monotonic nanoseconds
are causal diagnostics only; no calibrated timing uncertainty or tail estimate
is claimed. No physical effect or release test is needed because no input occurs.

## Environment, construction and retained failures

Actual environment: provided Linux x86_64 container, CPython 3.13.5, five visible
CPUs. Full interpreter hash/platform/monotonic-clock metadata is frozen in
ENVIRONMENT.json. Docker CLI/image identity is absent; this is not Docker Desktop
or OrbStack replication. No install, network experiment, model/provider, GUI or
OS input occurred. Fixed-source local filesystem fixtures only.

Excluded construction was exactly one four-cell matrix, all integral. Candidate
unit testing ran one method containing 15 assertions; its captured repeat and
exit are retained separately (pure construction only). Construction raw-only
audit rejected 12/12 corruptions. No construction or formal infrastructure failure
occurred in #3996. The intended exit-7 and partial-frame outcomes remain explicit,
not overwritten as normal completion. Old #3938 transcription failures remain
unchanged in their original namespace; publication was recovered via PR #3964.

## Complete retained evidence and read-only reproduction

`evidence/EVIDENCE.00.b64` through `.05.b64` form one lossless Base64/XZ file
bundle. It contains all 70 original source/evidence files: the frozen study,
construction and formal raw, every per-case trace/stream/seal where applicable,
actual stdout/stderr/exit logs, and both original audits. It is not a summary.

- Formal raw: 58072 bytes; SHA256
  `cd2f68f1360372c21307900e27f51614dcbba676f8dc66e7c29dee43a97cc904`.
- Original formal audit SHA256:
  `6846066e8572c88a9ad48c68532640000400698f3dccd406cb0dd0b3293041f0`.
- Full decoded bundle: 218045 bytes, 70 files; SHA256
  `20c954cf25578ed245c06c2c93bc8a72737779036b1ae2e7e1da95554df02ae2`.
- Source freeze SHA256:
  `a9fe3cf25dee73f1aefa642845b7fd7c4376ae5eceda62728441a1b0607a0dc5`.

Each of the six uploaded Git blob IDs matched its local expected object ID.
The bounded data-only unpacker checks parts, decompressed size/hash and member
paths before writing into a new destination. It never runs an experiment.
A clean local restore matched every original file. A separate restored raw-only
audit reproduced the original AUDIT output byte-for-byte. Existing-output refusal
returned exit 2. These are publication checks, not additional formal allocations.

From a repository checkout, choose a genuinely new destination:

```bash
python -S -B research/integration/passive_reader_finality_7f31_v1/unpack.py /tmp/issue3996-audit-new
python -S -B /tmp/issue3996-audit-new/study/audit.py /tmp/issue3996-audit-new/formal-01/raw.json > /tmp/issue3996-reaudit.json
cmp /tmp/issue3996-audit-new/formal-AUDIT.json /tmp/issue3996-reaudit.json
```

The raw-only auditor imports neither candidate nor runner/upstream and reconstructs
payloads, digests, cursor offsets/sequences, source identities, process receipts,
phase order and all decision denominators. It is a separate implementation and
process by the same assistant, not an independent person or second-machine study.

## Handoff and remaining roadmap

All proposed paths are additive under this one namespace; existing source modules,
#717/#3938 results and parallel #3931/#3933/#3941/#3947/#3952/#3977/#3978/#3984/#3988
are unchanged. Source freeze, one experiment, audit and exact publication are
complete. PR/checks/main readback are recorded separately rather than assumed.
Only owned, merged, dependency-safe branches are cleanup candidates; no other
worker's branch is disposable.

A real production producer/host must explicitly implement and validate its final
receipt contract before adopting this classifier. No seal should be inferred from
empty reads, exit codes alone or a model's statement. Host crash recovery and
producer epochs remain separate owned work. #3876/#57 and the full ROADMAP stay
open. Related transfer ideas: stream processing final markers, distributed-system
completion acknowledgements, and experimental provenance for partially completed
jobs; none becomes a validated production application from this fixture alone.
