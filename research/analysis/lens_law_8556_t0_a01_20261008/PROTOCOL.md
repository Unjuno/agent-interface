# Protocol

## H/T/D/C/U

**H — hypothesis.** For the declared finite observation/update model, the three scoped lens laws detect seeded adapter defects missed by final-label-only and same-input replay checks, while abstaining outside the stated assumptions.

**T — treatment.** A pure finite-state checker evaluates Get–Put, Put–Get, and Put–Put on explicitly declared worlds and semantic fields.

**D — design.** Twelve deterministic fixtures cover valid and benign-hidden controls; wrong-field, ignored, duplicate-callback, and first-write-wins defects; plus ambiguous applicability, stale epoch, partial domain, pending completion, completed async, and non-idempotence.

**C — comparison.** Compare a final projected-label-only oracle and same-request replay from the same initial state against the three laws. An independent auditor (does not import candidate.py) reconstructs results, checks the sealed truth table and digest, and rejects four mutation controls.

**U — uncertainty/scope.** This is an authored finite conformance model, not a live GUI, application, production route, WSL, or Docker experiment. Semantic equivalence applies only to each fixture's declared semantic fields. Declared totality/idempotence/side-effect properties are assumptions, and the finite worlds prove nothing outside the enumerated set. Async is represented only by a completion flag.

## Runtime and resource boundary

Run this no-I/O/no-network simulator with native Windows CPython 3.12.10. This is a narrow host-run exception while the shared WSLc/native-WSL workload lanes are held. It makes no container reproducibility or portability claim. No Docker, WSLc, or native WSL workload is involved.

## Formal execution and stop criteria

1. Freeze candidate.py, audit.py, input.json, truth.json, and this protocol; record SHA-256 digests before formal execution.
2. Record interpreter/platform and repository base SHA.
3. Run candidate CLI once, writing only the absent results/candidate.json.
4. Only if that exits successfully, run the independent auditor once, writing only the absent results/audit.json.
5. No retries, repairs, fixture edits, or second formal execution under this run ID. Failure is preserved; a repair requires a new run ID and successor record.
6. Success requires all 12 rows to match sealed truth; all four mutation controls rejected; targeted laws catch seeded defects; abstention controls do not PASS; and the two baselines miss the declared blind spots.
7. Stop after one candidate and one auditor invocation. Do not touch GUI, external services, user data, or shared WSL runtimes.
