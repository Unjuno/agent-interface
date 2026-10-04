# Logical-time unit-representation T1 — Issue #7327

Successor allocation `LOGICAL-TIME-SYMMETRY-7327-UNIT-T1-20261004-01`. This is a narrow fresh test of the unit-representation leg omitted by T0. T0's source, raw output, and scoped result remain unchanged; this allocation does not claim homogeneous-scale, quantization, backend, GUI, safety, or runtime equivalence.

## H/T/D/C/U

- **H:** Encoding every declared time field in seconds versus milliseconds, including `reference_period` and disturbance timestamps, then executing the same frozen exact-rational logical schedule, yields byte-distinct inputs but identical canonical event/state/held/release traces.
- **T:** Six Issue #7327 event schedules; exact `Fraction` arithmetic; explicit `s` and `ms` labels; frozen tie order (lease expiry, external transition, observation, hold deadline, task deadline, release). Candidate emits both source encodings and traces. A separately implemented raw-only auditor reconstructs both from `spec.json`, checks each converted field, and rejects four predeclared corruptions. Candidate once, auditor once, no retries.
- **D:** `PASS_UNIT_REPRESENTATION_SCOPED` only if all six paired raw inputs are distinct, all eight declared time fields and every event timestamp convert exactly (including reference period), normalized traces match, and the auditor rejects 4/4 corruptions. Any same-unit/no-op encoding, omitted time field, trajectory divergence, or missed mutation is FAIL/STOP as classified in `spec.json`.
- **C:** This checks a finite synthetic exact-time representation, not a real-time runtime. It does not validate a complete physical parameter inventory, nonzero fixed backend delay, quantization, asynchronous execution, or a live controller.
- **U:** Whether correct explicit unit representation is behaviorally invariant for this finite declared logical-time model.

## Execution policy

No candidate or audit is run until the source/input hashes are frozen and this allocation is recorded on Issue #7327. The preferred cached OrbStack image could not be inspected because its content blob lookup returns `operation not supported`; no image pull or container retry is authorized by this allocation. If retained, the eligible local run uses only Python's standard library on the host and makes no GUI/model/input/network calls. This environment choice limits the evidence to a deterministic CPU method test.

The single candidate invocation STOPped on a spec/schema mismatch; this first outcome is indexed in [STOP.md](STOP.md) and fully retained in [FAILURE.md](FAILURE.md). It is not retried in place; the corrected schema is a separate T2 allocation.

After preregistration, the single candidate and auditor invocations are:

```sh
python3 candidate.py spec.json output/candidate.raw.json
python3 audit.py spec.json output/candidate.raw.json output/audit.receipt.json
```
