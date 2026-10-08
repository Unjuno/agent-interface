# Issue #8620 T0: finite execution-information frontier

**Result: `PASS_METHOD_SCOPED` after a versioned post-result audit correction.** The candidate ran once. The first frozen auditor's `FAIL` is retained unchanged; auditor v2 read the same raw output and found its three failures were order-sensitive comparisons where the protocol specified field sets and unordered omission records. No candidate rerun occurred. This result covers only the authored finite fixture.

## H/T/D/C/U

- **H:** At a finite GUI-like task cut, future-contract-dependent equivalence classes can identify a smaller sufficient retained field set; reacquisition can recover selected discarded fields without losing proof-bearing state.
- **T:** Twelve histories with identical current screenshots, two future contracts, five schedule types, explicit proof fields and deterministic recovery costs. Compare full history, fixed window, task summary, and EIR retain/reacquire. Candidate and auditor are separate programs. The auditor independently reconstructs required fields, output equivalence classes, recovery cost, and mutation outcomes from the fixture.
- **D:** `PASS_METHOD_SCOPED` when both exact partitions and minimum field sets match; proof fields remain; EIR has no unavailable requirement; the changed contract changes the partition; EIR is Pareto-nondominated against both simple policies; and omission, false-equivalence, and proof-drop mutations are rejected. Auditor v2 confirms all conditions on the immutable candidate output. The frozen auditor v1 result remains `FAIL` and is not overwritten.
- **C:** A full-history policy is simpler and may be preferable when reacquisition is expensive or uncertain. Fixed windows can suffice when future obligations are narrow. The synthetic schedule probabilities and costs do not estimate real GUI costs.
- **U:** Field-atomic encoding and the declared finite contracts are assumed. No model, GUI, real application, memory pressure, latency, task success, or product benefit was tested. This does not establish an EIR runtime policy.

## Observed result

The candidate retained `selection` for `contract_v1` (24 synthetic storage bits over 12 histories) and `saved`, `selection`, `lineage`, `freshness`, and `authority` for `contract_v2` (132 bits). The contract expansion changed the partition from three classes to twelve. EIR recorded zero unavailable requirements under either contract. In `contract_v1`, EIR and fixed-window both had zero errors, while EIR used 24 versus 60 bits and the same expected recovery cost (0.5 units). In `contract_v2`, EIR had zero errors, fixed-window four, and task-summary five; EIR preserved the three proof fields and re-acquired declared-retrievable values at 0.65 expected units.

The first auditor invocation returned `FAIL` because it compared EIR field arrays and missing-field arrays in a specific order not required by the frozen contract. The independently implemented `auditor_v2_diagnostic.py` compares field sets and canonicalized omission records, recomputes all costs and partitions from the raw fixture, and detects all three injected mutations. Its `PASS_DIAGNOSTIC_ONLY` is a post-result raw audit, not a second candidate allocation. The original result is available at `audit/audit.json`.

## Provenance and reproduction

- Frozen source: `0621713407d42c5a3922572b2fe57222f175e9a2`.
- Freeze: [`FREEZE.json`](FREEZE.json).
- Input and raw output: [`input/fixture.json`](input/fixture.json), [`raw/candidate.json`](raw/candidate.json).
- First audit and diagnostic audit: [`audit/audit.json`](audit/audit.json), [`audit/audit_v2_diagnostic.json`](audit/audit_v2_diagnostic.json).
- Candidate command: `python3 src/candidate.py input/fixture.json raw/candidate.json` (exit 0; one invocation).
- Frozen auditor command: `python3 src/auditor.py input/fixture.json raw/candidate.json audit/audit.json` (exit 1; one invocation).
- Diagnostic audit command: `python3 src/auditor_v2_diagnostic.py input/fixture.json raw/candidate.json audit/audit_v2_diagnostic.json` (exit 0; one post-result audit of retained raw).
- Runtime: macOS 27.0 ARM64, CPython 3.14.5. The OrbStack `python:3.12-slim` image preflight stopped before candidate execution because the daemon could not open a content-store blob (`operation not supported`). Issue #8620 explicitly says T0 needs no container; host execution used the unchanged finite input and gates.
- Candidate input/source hashes are in `FREEZE.json`; raw and audit hashes are recorded in [`SHA256SUMS.txt`](SHA256SUMS.txt).

The prospective freeze was recorded on Issue #8620 before candidate execution. This is a finite method result only; T1 remains separately conditional and unrun.
