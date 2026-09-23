# Issue #4155 — typed failure-mode diagnosis first-rung result

Decision: **`FAIL_DIAGNOSIS_LAYER_UNNECESSARY`**.

This is a scientific negative result under the frozen equal-information deterministic contract, not an integrity failure. The explicit diagnostic mode layer classified the authored faults correctly, but it did not improve the final bounded-recovery decision over a direct observable→recovery mapping with the same inputs and representational capacity.

## Formal result

One formal invocation; 324/324 frozen rows; reruns/replacements/tuning 0.

| metric | DIRECT_RECOVERY | MODE_THEN_RECOVERY |
|---|---:|---:|
| wrong recovery | 0 | 0 |
| unnecessary YIELD | 0 | 0 |
| unsafe non-YIELD on ambiguous/contradictory evidence | 0 | 0 |
| authority escapes | 0 | 0 |

Additional gates:
- final disposition mismatches between DIRECT and MODE: **0/324**;
- independently identifiable single-fault rows: **16/324** (four fault signatures × four irrelevant variations);
- all-normal, any UNKNOWN, contradictory and multi-fault rows fail closed to YIELD;
- semantic/input authority are false on every row.

The independent raw-result auditor reconstructs the full 3^4 × 4 corpus without importing the candidate and returns `errors=[]`. Twelve coherent result/source/provenance corruptions are rejected 12/12. Postformal contract tests remain 4/4 PASS and all frozen source SHA-256 values are unchanged.

## Interpretation

For deterministic functions over the same evidence, `MODE_THEN_RECOVERY(x) = R(D(x))` can be represented directly as `DIRECT_RECOVERY(x)`. The formal corpus confirms that this equivalence is not merely algebraic for the frozen GUI-failure vocabulary: both arms make the same safe final decision on every row. Therefore Issue #4155's first-rung decision-quality hypothesis is not supported unless the comparison introduces a genuinely different factor such as learned generalization, feature abstraction, explanation/maintenance cost, partial observability, or transfer.

Do **not** create a successor that merely makes DIRECT artificially weaker (for example symptom-only) and then attributes the resulting gap to diagnosis. A valid successor must change a scientifically meaningful capability or environment.

## Scope

Provided Linux x86_64 execution container, CPython 3.13.5, standard library only. No live GUI, OS task input, model/provider, network experiment, user data, learned classifier, latency/token measurement, multi-fault diagnosis, recovery execution or production-runtime claim.

## Evidence identities

- FORMAL_RESULT.json SHA-256: `ca448279282edeb605114b7e641dca4564fcc2291db2131e964cfee86f65b8e8`
- AUDIT.json SHA-256: `4af44b93dbc530e3a09bfcdab764fe995609f7d3473b1848c5193cb4426f16e6`
- CONTROLS.json SHA-256: `124ca2f3ed04360a7d4649057b53438fa42f373320e46806fbc33f1999e4a2f6`
- frozen experiment.py SHA-256: `b942e9104fb94f2b6f5ca3b303873d5089ab81b14648021db2ccce132c584779`
- frozen independent audit.py SHA-256: `c3eeef3ce354b45bffaa6f392092b7b767e06b017c23c253efb3aec73a14de46`

## ERROR CHECK

- formal invocations: 1
- reruns: 0
- replacements: 0
- post-result gate/source tuning: 0
- candidate/oracle mismatches: 0
- DIRECT/MODE final mismatches: 0
- audit errors: 0
- corruption controls rejected: 12/12
- postformal source drift: 0
