# Issue #4844 preregistration — typed mode under partial observation

Allocation: `typed-mode-generalization-4844-seed-484401-v1`
Intake/main: `d2219a2db20315473eed09818d574de5b5966b75`
Branch: `research/typed-mode-generalization-4844-seed484401-20260927`
Path: `research/experiments/typed_mode_generalization_4844_v1/`

## H — hypothesis
Under partial/noisy cues, factorizing safe-disposition choice through a five-class latent mode posterior may reduce wrong emitted recovery actions versus directly fitting safe disposition, but can reduce coverage and may fail on compositional blocks. No direction is assumed.

## T — frozen comparison
- Python stdlib only; deterministic Bernoulli Naive Bayes with equal Laplace alpha=1 on identical observations/training rows. DIRECT_RECOVERY fits the three safe dispositions. MODE_THEN_RECOVERY fits five modes and aggregates complete mode posterior by frozen map [0,0,1,2,2].
- Six binary caller-visible cues; five frozen prototypes [[0,0,0,0,0,0],[1,1,1,1,1,1],[0,1,0,1,0,1],[1,0,1,0,1,0],[0,0,1,1,0,1]]. Shared symptom is constant/omitted from input. Per observed cue, independent flip probability .08 and independent missingness .20. Confidence threshold .70; below threshold abstain (no emitted disposition).
- Train: seed 484401, 2,000 balanced mode rows. Heldout: seed 484402, 3,000 rows, 750 each, with blocks all_missing_cue1, all_missing_cue4, two_missing_cues, contradictory (last block flips cues 0 and 5 before missingness). Row order and RNG are fixed in `experiment.py`.
- Full-observation control: one noiseless prototype per mode. Unknown control is six missing cues. Contradictory fail-closed control [0,0,0,1,0,1] was selected via exhaustive 64-vector construction-only scan on the training fit and is not a heldout row.
- Pinned local container `python:3.11-bookworm`, image ID `sha256:e635facd4cd70a0e0b5d72cb0ce38f24434b6e98e11c2383d428a880c0f7232c`, linux/amd64. Command: `docker run --rm --pull=never --network none --read-only --cpus=1 --memory=512m --pids-limit=32 -v <source>:/src:ro -v <fresh-output>:/out -e OUT_DIR=/out python:3.11-bookworm python /src/experiment.py`. No GPU, external model, network, tune, retry, or hidden features.
- Frozen source SHA256: experiment.py `31d5cebd2d4cf348780ad6f6b14b86fc8921e115a05ad6c3c5449cdbabaaa6e9`; audit.py `593cb9b4fe3d64df22186ca74cae7acc9cec3a52439d48692f71fd5b05b5aef7`. Construction-only compilation already passed; formal output directory must be empty. Independent audit validates exact row accounting/summary recomputation, controls, and rejects allocation/row-count corruptions (2/2).
- No model fits or separate formal allocations; one deterministic synthetic diagnostic invocation only. Preserve stdout, result JSON, audit receipt, invocation/container receipts.

## D — frozen interpretation
For each of the four blocks, a block qualifies only if typed mode reduces wrong *emitted* dispositions by >=25% versus direct and loses <=5 percentage points of safe coverage, with zero unsafe emissions. All blocks are reported individually. PASS_TYPED_MODE_GENERALIZATION_SCOPED requires at least one partial/compositional block to qualify, full-observation control correct and equal, unknown/contradictory controls abstain in both arms, and independent audit errors=[].
FAIL_DIAGNOSIS_STILL_REDUNDANT if no block qualifies and coverage does not exceed its loss bound. HOLD_COVERAGE_TRADEOFF if an apparent error reduction comes with >5pp coverage loss or block results are mixed. FAIL_MODE_MISROUTES_RECOVERY if any unsafe emission or either control fails closed. Provenance/audit failure is STOP, not a scientific result.

## C — limits
This is one authored synthetic cue family. Bernoulli factorization and prototypes determine difficulty; it cannot establish real GUI diagnosis, cross-app transfer, production trust, authority, latency, or any GPU benefit. The threshold and controls were frozen before the single heldout run.

## U — integration
No runtime integration or authority change. A valid result only informs whether a richer preregistered multi-seed/realistic successor is worthwhile. Prior Issue #4155 and PR #4169 remain untouched.

## Construction receipt
The source compiled with `python -m py_compile`. A construction-only Docker run (before the frozen source hashes above) exercised the generator, found the contradictory control vector by exhaustive scan using training fit only, and was not read as formal test output.