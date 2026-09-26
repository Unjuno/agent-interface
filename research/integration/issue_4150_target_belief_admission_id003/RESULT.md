# Issue #4150 — ID003 finite target-belief admission experiment

## H / T / D / C / U

**H.** Keeping multiple target candidates is useful only if action admission does not collapse unresolved belief to top-1. With the frozen minimum score, closed margin threshold, provenance and declared safe-probe bit, the belief-aware rule should permit input authority only for sufficiently separated, valid evidence; ambiguity should return `PROBE` or `NEEDS_DECISION`; invalid/weak evidence should be rejected. The deliberately incomplete top-1 comparator should false-allow the ambiguous profiles.

**T.** Fresh allocation `target-belief-admission-4150-20260927-03`, exactly one formal invocation, 8 score profiles × 4 provenance states × 2 probe states = 64 rows. OrbStack Docker, Python 3.12.14, `linux/amd64` (`uname -m`: `x86_64`), image ref `python:3.12-slim`, local image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; `--network none`, read-only container/source, fresh writable output mount. No GUI, model, provider, input action, network experiment, or user data.

Exact formal command:

```sh
docker run --rm --platform linux/amd64 --pull=never --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  -v /tmp/issue4150-id003/src:/src:ro \
  -v /tmp/issue4150-id003/evidence:/out:rw \
  -w /src -e PYTHONPYCACHEPREFIX=/tmp/pycache python:3.12-slim \
  python experiment.py --out /out/FORMAL_RESULT.json --source-dir /src
```

**D.** Raw decision: `PASS_TARGET_BELIEF_ADMISSION_CONTRACT_SCOPED`. The 64 rows satisfy candidate false ALLOW 0; top-1 false ALLOW 6; safe candidate ALLOW 6; counts ALLOW 6 / PROBE 3 / NEEDS_DECISION 3 / REJECT 52; oracle mismatch 0; authority errors 0. Independent raw-only audit: `pass=true`, `errors=[]`. The retained mutation-control run tried 12 transformations and rejected 10. Transformations 2 and 4 were no-ops because row `r00` already had candidate/oracle decision `ALLOW`; therefore the control harness's all-12 boolean is `false`, while the preregistered minimum of 10 coherent corruptions rejected is met. Preserve this control-harness weakness; do not call it 12/12.

Formal invocations: 1. Reruns, replacements, threshold changes, and post-freeze source changes: 0.

**C.** Scores, safe-to-act labels and probe availability are authored finite-contract fixtures, not natural detector measurements. The top-1 comparator is intentionally incomplete and is not asserted to be production behavior. A contract PASS is not a live visual-target, GUI-action, task-effect, model, latency, cost, or product PASS.

**U.** Natural ambiguity frequency, visual detector calibration, occlusion/distractor behavior, safe-probe side effects, planner/model decisions, GUI task completion, production integration, cost/latency and cross-domain behavior remain untested.

## Provenance and retained predecessor outcomes

- Source/freeze commit: `cfe8c47c2c2ec8cb81de4ac7932efa1ab152e14e`, parent main `91b5143989403754b360738c445f72b68b673718`; allocation was frozen on Issue #4150 before the formal invocation. Source files and SHA-256 values are retained at `research/analysis/target_belief_admission_v3/`.
- ID001 remains `STOP_LOCAL_SOURCE_MATERIALIZATION`, 0/64 scientific rows; it was not rerun. Its recovered source capsule hash-matched and its excluded Docker construction check passed 6/6.
- ID002 remains `STOP_SOURCE_INTEGRITY`, 0/64 rows: its manifest claims a 6,228-byte capsule/SHA `bfd842df86e78d7bf3ef0b5c5b3fcffd80f0126a6762fbb10a6eebe659d24901`, but the frozen branch does not contain the capsule. ID002 was not reconstructed or rerun.
- Metadata discrepancy retained: the inherited `ENVIRONMENT.json` says CPython 3.13.5, while ID003's frozen `FREEZE.json` and actual Docker run specify/observe CPython 3.12.14. Runtime/source identity and execution are recorded exactly; no source was edited after freeze. This is a provenance defect to correct in a future fresh allocation, not evidence against or in favor of the finite decision rule.

## Raw artifact hashes (SHA-256)

- `FORMAL_RESULT.json`: `6a391d2496c82282c66446213fdfc46e437baa512e4100697bc431a307a5d490`
- `INDEPENDENT_AUDIT.json`: `7f9095a0445ad0cba954479f52f849be879680eeb690a299ce01dbc42035ef28`
- `MUTATION_CONTROLS.json`: `ec2f82168fb18ba6d6b92755f105a625b54ec2d5370e7a6efb73a72e13af874a`

The finite authored contract passed on this exact allocation. The two STOPs and the mutation-harness false result remain separately visible; no broader runtime claim follows.
