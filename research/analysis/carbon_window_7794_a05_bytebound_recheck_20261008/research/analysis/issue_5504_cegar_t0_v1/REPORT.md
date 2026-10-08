# Issue #5504 — T0 synthetic counterexample-guided refinement

## Result

**T0-02: `PASS_SYNTHETIC_CEGAR_BOUNDARY_SCOPED`.** The frozen 16-case corpus passed the separate raw-only audit with zero errors. The first formal allocation, T0-01, remains an unchanged runner STOP and was not retried; T0-02 is its separately frozen runner-repair successor.

| Held-out metric | Coarse (1 check) | CEGAR (5 checks) | Full fixed (5 checks) | Over-specific fixed (8 checks) |
|---|---:|---:|---:|---:|
| False admissions | 4 | 0 | 0 | 0 |
| False rejections | 0 | 0 | 0 | 1 |
| UNKNOWN preserved | 2/2 | 2/2 | 2/2 | 2/2 |
| Authority grants | 0 | 0 | 0 | 0 |

CEGAR added four checks with traceable replayable training parents: `authority_current`, `evidence_current`, `effect_safe`, and `acyclic_dependencies`. The initial `target_current` check already caught the target-replacement counterexample. The two-node training cycle and three-node held-out cycle both rejected. The five-check full static ontology matched the independent oracle for all 16 cases. The eight-check comparator added three predeclared irrelevant attestations and consequently falsely rejected one valid held-out case.

Construction suite: 12/12 tests passed in the pinned Docker image before formal execution. Mutation tests reject altered candidate decisions, metrics, authority claims, corpus data, and orphaned refinement lineage. Formal T0-02 candidate and auditor each ran once, in separate network-disabled containers.

## Preserved execution history

- **Preflight construction transport STOP:** first Docker mount form failed before a container started; retained at `results/preflight/docker-mount-stop.json`. A corrected read-only mount form then ran construction tests.
- **T0-01:** one formal candidate invocation computed in memory, then `STOP_RUNNER_FREEZE_SCHEMA_KEY_ERROR` before writing output because the runner read the wrong JSON key. No scientific disposition is inferred, no auditor ran, and the allocation was never retried. Exact record: `results/t0/STOP.json`; the frozen package is `FREEZE.json`.
- **T0-02:** a new allocation ID, runner entrypoints and empty output path; same frozen corpus, arms, oracle and gates. Candidate wrote once; a second container independently audited once: `PASS`, errors `[]`. See `FREEZE_T0-02.json` and `results/t0-02/RUN.json`.

## Interpretation and limits

This result supports only a finite synthetic boundary: for these authored predicate mutations, a traceable refinement loop avoided four coarse held-out false admissions while preserving two UNKNOWNs, and it used fewer checks than the deliberately eight-check comparator. It does **not** show an efficiency advantage over the five-check complete static ontology: CEGAR learned all five required checks. The over-specific comparator is intentionally strict and is not a universal baseline. Training and held-out families share predicate types, and both the oracle and auditor are code-authored rather than independently human-authored.

No live traces, real verifier, model, GUI, runtime authority, safety benefit, latency/cost reduction, ontology completeness, or cross-domain transfer were tested. This does not establish CEGAR suitability for production or close Issue #5504's broader question.
