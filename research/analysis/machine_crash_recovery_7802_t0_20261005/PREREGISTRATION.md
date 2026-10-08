# Issue #7802 T0 preregistration — machine-crash recovery model

Allocation: `MACHINE-CRASH-7802-T0-20261005-01`  
Frozen source base: `main@21fecd58b9de30073c97234124e73b78c67d4b0c`  
Additive package: `research/analysis/machine_crash_recovery_7802_t0_20261005/`  
Candidate and auditor retries: 0 each.

## H / T / D / C / U

**H.** At least one durable machine-crash image in the frozen persistence model is absent from its corresponding process-crash control. The recovery classifier must return `UNKNOWN_RECONCILE` when a separately stored effect and receipt disagree, and must never infer completion from a local receipt without independent effect confirmation. This T0 is a method/model test; it cannot pass the Issue's host-stack H hypothesis.

**T.** Run the deterministic standard-library model in `fixture.json`. The fixture covers: buffered receipt write; file `fsync`; atomic rename; directory `fsync`; external-effect commit; same-store atomic commit; separate-store effect/receipt orderings; post-commit/pre-ack; loss/reordering/torn writes allowed only at declared machine-crash cuts; and invalid-checksum recovery. Each scenario carries an explicit process-restart image and the complete hand-authored set of machine-crash images permitted by the fixture's stated persistence contract. An effect state is independent-oracle input, never inferred from the receipt. The candidate emits one row per image. A separately implemented raw-only auditor reconstructs all classifications and rows from the frozen fixture, compares process and machine state sets, and applies four output mutations.

Execution is CPU-only with Python's standard library. No real filesystem durability, SQLite VFS, OS/device crash, VM power cut, WSL/WSLc, Docker, network, GUI, model, input, or external effect is exercised. The machine images are a finite authored model, not measurements of the current host. The actual T1 from Issue #7802 remains separately gated on an isolated VM and validated abrupt-poweroff harness.

**D.** `PASS_METHOD_SCOPED_T0_ONLY` iff (1) the independent auditor reconstructs every emitted row and classification; (2) every listed mutation is rejected; (3) at least one machine-only state exists; and (4) all inconsistent/unknown effect-receipt pairings resolve to `UNKNOWN_RECONCILE`, while corrupt/torn receipt states are `CORRUPT_OR_UNTRUSTED`. Otherwise retain the first `FAIL` or `HOLD` without rerun. No T1/H classification follows from a method pass.

**C.** The fixture's persistence contract may be too permissive or omit a real filesystem behavior. A production effect oracle may be unavailable, making more states unknown. Same-store atomicity can eliminate split states only when the effect is truly in that store. The authored matrix may not represent any actual application protocol.

**U.** Finite synthetic protocol/image model only. No current Agent Interface journal behavior, filesystem/SQLite durability, power-loss behavior, exactly-once execution, safety, or retry policy is validated. The state-classification result is bounded by the explicit fixture and oracle labels.

## Freeze and one-shot procedure

The allocation source is frozen by the source commit recorded on Issue #7802 before either formal invocation. The exact source commit and SHA-256 values for `candidate.py`, `auditor.py`, `fixture.json`, `test_construction.py`, and this preregistration will be retained in `FREEZE.json`. Construction tests run before source freeze and are not formal candidate/auditor invocations.

After freeze, run `candidate.py` exactly once, then run `auditor.py` exactly once against its untouched output. Save stdout, stderr, exit codes, and the audit JSON. Do not repair, rerun, or relabel a formal failure. Any corrections require a new additive successor allocation.
