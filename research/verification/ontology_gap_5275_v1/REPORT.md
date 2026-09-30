# Issue #5275 ontology-gap T0 report

## Disposition

**FAIL_DETERMINISTIC_GAP_FALSE_PASS**. The deterministic schema/coverage detector caught explicit unknown primitive, unknown evidence role, and malformed-check cases, with zero IID abstentions. It silently treated two semantically unsupported Agent Action plans as covered.

| Measure | Result | Frozen gate |
|---|---:|---:|
| Cases | 9 | 9 |
| Oracle OOD / UNKNOWN cases | 5 | 5 |
| OOD false passes | 2 | 0 |
| IID false abstentions | 0 | 0 |
| Independent audit integrity errors | 0 | 0 |
| Dispatch / model / GPU / network / authority grants | 0 / 0 / 0 / 0 / 0 | all 0 |

False-pass cases:
- `ood-unmodeled-external-recipient`: known target/postcondition checks did not expose missing recipient authorization and irreversible-disclosure checks.
- `ood-adversarial-familiar-legal-hold`: known target/reversibility checks did not expose the missing legal-hold check.

`PLAN_COVERED` is not an action PASS, permission or dispatch. In this harness, however, it fails the required conservative novelty boundary: downstream consumers must not assume this output excludes hidden missing checks.

## Frozen H / T / D / C / U

See [PREREG.md](PREREG.md), frozen before the formal invocation. Intake main was `322faf504a5ac993b092f154733d83bc13767e60`; source, runner, fixtures, tests and auditor are retained additively under this directory.

## Executed command and environment

One host-only, memory-streamed run from exact GitHub readback sources; no local result files were written.

- Construction: Python 3.11.9 with `-B`; all 7 tests passed before the one-shot T0.
- Formal runner: `python -B -c $bootstrap`. The bootstrap registered the exact read-back `registry.py` source as module `registry`, then executed exact read-back `run_t0.py` using `exec(compile(...))`. Runner source Git blob SHA-1: `dbea4672730b8617e29cdeeb63df37c3657d423d`.
- Independent audit: separate `python -B -c $bootstrap` process executed exact read-back `audit_t0.py` (SHA-1 `62d1e2a9991e7bddf511e40c5b74597877fc1b23`) against the raw JSON passed through an environment variable; it does not import or invoke the candidate.
- Runtime: Windows (`win32`), CPython 3.11.9.
- Registry blob SHA-1: `d7e35205daf8b7385a189ef5d1a78bd07ded3cbd`; corpus blob SHA-1: `81e15afc954eac6687269ff5971d690bb1170208`; tests blob SHA-1: `3cc9e63b73b19c00d8ba7e3521f786a253f25d36`; preregistration blob SHA-1: `55dd5ac94ffe560f4abf1b5afe55d46c364e6696`.
- Raw first outcome: [FORMAL-01.json](FORMAL-01.json). Independent raw-only result: [AUDIT-01.json](AUDIT-01.json).

The repository method prefers a container when feasible. This run was deliberately limited to deterministic host CPU execution: C: had 0 bytes free, while the shared container/GPU queue showed unresolved allocations. No Docker invocation, model load, GPU operation, network call, GUI/input or verifier dispatch occurred. The raw record says `container:false`; this is not container-backed formal evidence.

## Interpretation / limits

The finite result falsifies the claim that typed allow-list/schema coverage alone is sufficient for this adversarial semantic set. It supports retaining a mandatory UNKNOWN/escalation boundary, but it does not validate any learned router or combined detector. No trained confidence arm was tested; no semantic generalization, escalation behavior, real verifier truth, safety gain, latency, task/GUI outcome or ontology completeness is established. Synthetic labels and task summaries were authored for this finite discriminator. No post-hoc tuning or rerun was performed.
