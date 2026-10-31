# Frozen protocol — Issue #8576 T0 A02 mutation-gate requalification

## Question and scope

This separately scoped successor tests whether the formal independent auditor actually executes and rejects the six output mutations required by A01's protocol. It directly addresses the append-only qualification at https://github.com/Unjuno/agent-interface/issues/8576#issuecomment-6058217467: A01's reconstruction evidence remains narrowly supported, its aggregate PASS remains unsupported, and none of A01's frozen files or consumed outputs are modified or rerun.

The candidate receives only `input.json`; `truth.json` is auditor-only. The 12-case deterministic synthetic fixture, hidden-label pairing, abstention rules, provenance requirements, no-action authority, freshness warning, and bounded method claim are retained. This run cannot establish human usefulness or benefit. No participant study, GUI/model interaction, continuation action, real user data, or product integration is authorized.

## Frozen mutation gate

The auditor independently reconstructs the unmodified candidate output and then creates six named mutated copies: invented suggestion for an ambiguous case; suggestion from stale state; substituted source ID; granted continuation authority; guaranteed-freshness promise; and hidden-label leakage. Each mutated copy is submitted to the same independent reconstruction/validation gate. The auditor records one row per mutation with its name, actual rejection boolean, and exception reason. The gate passes only if exactly all six are rejected and each has a nonempty reason. A missing control or accepted mutation is a formal failure. The fixed count alone is never evidence.

The fixture/truth and mutation definitions are fresh A02 files. Unit tests verify that the formal gate records six executed rejections and fails when one control is absent. These tests are construction checks; only the one-shot frozen auditor output is formal evidence.

## H/T/D/C/U

- **H:** For this finite fixture, the independent reconstruction function rejects each of six concrete semantic/provenance mutations to an otherwise valid candidate result.
- **T:** After freeze, run the candidate once, then (only if exit 0) run auditor once. Auditor reconstructs 12 rows and executes six mutations with exclusive output creation. Preserve stdout, stderr, exit codes, wall-clock bounds, and hashes.
- **D:** `PASS_METHOD_SCOPED` requires 12/12 exact independent reconstructions, zero errors, identical public decisions for the paired hidden-label cases, exactly six named mutation records, each actually rejected with reason, zero authority/freshness violations, and exit 0. Any accepted/missing mutation is `FAIL_MUTATION_CONTROL`; any reconstruction or provenance mismatch is `FAIL_AUDIT`; a pre-pair infrastructure barrier is retained as `STOP`. No retry, pooling, replacement, or threshold adjustment.
- **C:** The mutants are authored representatives, not an exhaustive adversarial search; sharing one validator for base and mutant rows may miss a common-mode error. The topological-order reconstruction remains independent from the candidate's frontier algorithm but is not a human-use test.
- **U:** Synthetic finite-schema method evidence only. No claims about effort, accuracy in real use, anchoring, return-to-task, product quality, or human benefit.

## Runtime and execution controls

Use the locally available Python 3 interpreter with network access unused. Before formal execution, record the interpreter version and source/data SHA-256 values in `FREEZE.json`, commit the complete freeze, and run only the one-shot candidate/auditor pair against that commit. Candidate and auditor outputs use exclusive-create mode. Any first formal launch or failure is retained; never rerun this allocation.
