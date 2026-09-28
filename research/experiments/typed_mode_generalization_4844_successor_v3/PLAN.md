# Issue #5184 — fresh-seed typed-mode successor

## Lineage and preservation

Successor to #4844's consumed allocation. Preserve #4155/#4169, #4844/#4863, their raw evidence, source, outcomes, and labels unchanged. #4844's 3,000-row run remains `STOP_PROVENANCE_OR_AUDIT`; its metrics are not inferential. The 4,800-row #4844 comment whose links point to the #4155 evidence path is retained as an unresolved provenance conflict and is not pooled.

Allocation -01 was retired before formal freeze as `STOP_PREFORMAL_SEED_EXPOSURE`: construction test code accidentally invoked the full generator on candidate seeds 484411/484412. Allocation -02 then stopped before container creation because a manually entered Docker image ID omitted `681`; Docker returned exit 125. Neither allocation produced formal data, and all four seed values are retired from reuse. Current allocation -03 uses fresh 484431/484432; construction tests use only 17003/17004. The Docker image argument must be read from the frozen JSON at runtime and checked against `docker image inspect` immediately before launch; do not transcribe it.

- Current-main intake: `dbfae29cf848e4beee8f0287a9843532f5a695a8`.
- Branch: `research/typed-mode-4844-successor-v3-20260928`.
- Additive path: `research/experiments/typed_mode_generalization_4844_successor_v3/`.
- Formal executions allowed: one runner, then one separate auditor; no retry.

## H / T / D / C / U

**H.** Under the authored five-mode/six-cue synthetic family, factorizing a recovery classifier through a five-class mode posterior may reduce wrong emitted recovery decisions on partial/compositional holdouts, at a possible safe-coverage cost. Direction is not assumed.

**T.** Compare `DIRECT_RECOVERY`, a three-class Bernoulli naive Bayes classifier, with `MODE_THEN_RECOVERY`, a five-class Bernoulli naive Bayes classifier whose complete mode posterior is aggregated by disposition map `[0,0,1,2,2]`. Both receive identical six-cue rows, share Laplace alpha=1, cue flip p=.08, and emission confidence threshold .65. Train 2,000 balanced rows from seed 484431; evaluate 4,800 rows from independent seed 484432, 960 per block (192 per mode):

| Block | Frozen input transformation | Random missingness |
|---|---|---|
| COMPLETE | none | none; cue flips only |
| SINGLE_MISSING | force cue 1 absent | p=.20 on all cues |
| MULTI_MISSING | force cues 1 and 4 absent | p=.20 on all cues |
| COMPOSITION_HOLDOUT | invert cues 0 and 5 before missingness | p=.20 on all cues |
| NUISANCE_SHIFT | invert cue 3 before missingness | p=.20 on all cues |

All blocks receive independent p=.08 binary cue flips. TRAIN uses p=.20 random missingness. Full-observation controls use the five noiseless prototypes. Unknown is all cues missing; contradictory control is `[0,0,0,1,0,1]`. Construction test seeds are 17001/17002 only and are excluded from all formal estimates. `audit.py` is an independent raw-only implementation: it does not import the candidate and recomputes row truth, denominator, per-arm errors, coverage, controls, and frozen decision gates; it rejects 16 evidence mutations, noncanonical bytes, and duplicate JSON keys.

The local Desktop image is pinned by ID `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`, `linux/amd64`, CPython 3.12.14. Use `desktop-linux`, `--pull=never`, network none, read-only root/source, CPU 1, memory 512 MiB, PIDs 32, no-new-privileges, tmpfs-only `/tmp`, and fresh distinct runner/audit output directories. The runner sees no writable source path; the auditor sees raw evidence read-only and writes only to `/audit`. Freeze and verify every source Git blob, SHA-256 and byte count before formal invocation. No model, GPU, GUI, OS input, user data, external network, or shared OrbStack resource.

**D.** `PASS_TYPED_MODE_GENERALIZATION_SCOPED` only if each primary block (SINGLE_MISSING, MULTI_MISSING, COMPOSITION_HOLDOUT) independently has at least 25% relative reduction in wrong emitted dispositions, no more than .05 absolute coverage loss, and zero unsafe emissions; COMPLETE predictions equal and correct; unknown and contradictory controls abstain in both arms; all 16 corruption controls reject; and the independent audit has zero errors. NUISANCE_SHIFT is reported but cannot substitute for a primary block. Valid no-benefit is `FAIL_DIAGNOSIS_STILL_REDUNDANT`; apparent gains with >.05 coverage loss are `HOLD_COVERAGE_TRADEOFF`; other valid mixed/insufficient results are `HOLD_MIXED_PARTIAL_RESULT`; unsafe emission or failed controls are `FAIL_MODE_MISROUTES_RECOVERY`. Provenance/resource/audit failure is `STOP_PROVENANCE_OR_AUDIT`, not a scientific result.

**C.** One finite seed pair and one authored simulator; direct and mode factorization have different inductive biases. A scoped result is not a population estimate.

**U.** No real GUI diagnosis, cross-app transfer, product/runtime readiness, authority or safety, latency/token benefit, or GPU/model quality claim.

## Stage-0 exclusion

Host Stage-0 runs only the registered test seeds 17001/17002. It checks construction, accounting, source identity, deterministic audit logic, and corruption rejection. It must not invoke defaults that select the formal seeds. Its synthetic rows are not formal data.
