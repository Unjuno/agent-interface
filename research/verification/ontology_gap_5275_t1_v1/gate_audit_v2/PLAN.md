# Additive gate-audit correction for PR #5457

This is retained-input maintenance verification, not a new Issue #5275 science
allocation. Original head: `bbf43bf7a569e9c79883756bef41cf7677e50239`.
Original `FORMAL-01.json` SHA-256:
`ce1219edc12ed3526c0be90043bfe3428db3d36e42c6337e6f532e18ae2c72d6`.
All predecessor files and verdict text remain byte-identical.

## H / T / D / C / U

H: a verifier deriving the complete declared gate map independently can reject
missing, extra, altered, or wrong-type gates without accepting an invalid PASS
or rejecting coherent falsifying evidence merely because it is a FAIL.

T: read only the retained raw and corpus. Independently tokenize and reconstruct
the 13 row outcomes and complete arm metrics without importing or executing
candidate.py or run_t1.py. Reconstruct the exact three gates. Require exact
Boolean types and exact keys; derive verdict from reconstructed gates only.
The actual CLI pins corpus and candidate bytes to the retained source hashes.
The pure audit function additionally receives test-only reference fixtures to
exercise a coherent genuine FAIL: one supported description contains only OOV
words, so the independent reconstruction yields one false abstention. This
fixture is constructed test data, not a newly observed scientific outcome.

Controls include the original auditor on retained raw copies with empty,
missing, extra, integer-valued, and coherently flipped gates/verdict; successor
rejection of those copies; a valid FAIL fixture; attempted promotion of that
FAIL to PASS; invalid row/count/metric/score controls. These are local data
integrity tests, with no external inputs or service calls.

D: maintenance PASS requires original raw accepted, every frozen negative
control rejected, valid FAIL accepted as integrity-valid FAIL, source/raw bytes
unchanged, and the separately executed successor CLI returning the independently
reconstructed original disposition. Any failed assertion or timeout remains
FAIL/STOP and is retained. This does not rewrite the original audit's historical
coverage or any original scientific verdict.

C: the old auditor's row consistency checks already constrain actual scientific
outputs. The discovered defect primarily permits unvalidated gate metadata and
disposition flips. Rejecting corrupted metadata is not evidence that the
observed original phrase-separation result was false.

U: finite synthetic corpus; all six supported evaluation texts duplicate
training texts. No held-out semantic generalization, task effects, GUI/runtime
correctness, container/Docker, model, throughput, or security certification.
Declared side-effect zeros are metadata consistency checks, not independent
observation of the original execution. JSON lexical duplicate-key handling,
hostile reference corpora, and unbounded schemas are outside this correction.

## Execution boundary

Only this additive directory may be changed. Construction tests run before
freeze and may iterate with meaningful failures retained. Independent reviewer
approval precedes one bounded retained-input verification invocation. No
scientific candidate/runner calls, remote changes, or dedicated hosted jobs.
Linux CPU affinity is narrowed to one allowed CPU; RLIMIT_AS is 256 MiB per
process; CPU time limit 15 s per process; outer wall envelope 30 s. Two sequential
small Python processes may briefly overlap while the parent waits for the CLI;
this is not a cgroup aggregate-memory reservation. Output is exclusive-create,
so the verification cannot silently overwrite a previous receipt.

Planned command, from the repository root:

`timeout 30s python3 -B research/verification/ontology_gap_5275_t1_v1/gate_audit_v2/verify_retained.py --out <fresh-directory>`

The wrapper records source hashes, exact argv, environment/limits, original
auditor controls, successor CLI stdout/stderr/exit, tests and source readback.
Parent coordinates publication and author concurrency separately.
