# Formal report — Issue #3918

## Decision

`FAIL_TARGETED_SHIFT_AUGMENTATION`. The paired intervention improved near-boundary CORRECT recall substantially over the balanced controls, but the preregistered all-seed acceptance contract was not met. This is a synthetic, authority-neutral proposal classifier and is not execution authorization.

## Frozen experiment

- Three paired seeds: 3470, 3471, 3472; control vs treatment; six 700-step CPU trainings.
- Treatment replaced 1,024 of 2,048 CORRECT training rows with near-boundary examples. Initialization and minibatch-index streams were paired per seed.
- Container: local `needle-pilot05:local`, image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`; CPU-only, no network, read-only source/root, 2 CPUs, 4 GiB, 64 MiB tmpfs.
- One formal invocation; no retries. Construction suite passed 11/11 before the freeze.

## Treatment results

| Seed | Shift accepted accuracy | Shift CORRECT recall | CORRECT coverage | False-CORRECT fraction | IID accuracy | p95 latency (ms) | Shift-quality gate |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 3470 | 0.9442 | 0.8235 | 0.7969 | 0.000977 | 0.9981 | 0.0509 | FAIL |
| 3471 | 0.9715 | 0.9112 | 0.8027 | 0.000977 | 0.9996 | 0.0465 | FAIL |
| 3472 | 0.9959 | 1.0000 | 0.7969 | 0.003255 | 0.9965 | 0.0382 | PASS |

Paired CORRECT-recall lifts vs control were 0.8235, 0.9100, and 0.5551. Thus augmentation helped this metric in all three seeds, but only one treatment seed cleared the preregistered per-seed shifted quality gate; all three were required. Boundary YIELD, invalid-input YIELD, IID accuracy, false-CORRECT cap, and latency gates passed for all treatment seeds. Overall experiment decision remains FAIL, not a successful validation.

## Integrity and artifacts

Independent audit: `PASS`, zero errors; it reconstructed the training-row and minibatch-stream digests, verified paired setup and evaluation records, and recomputed the preregistered decision. Scientific gate failure is separate from evidence integrity.

- `FORMAL_RESULT.json` SHA-256: `951622f0a1cbd4da51520d4597bcf9b19c7bf016c6292d24a44d85df4995ddb2`
- `AUDIT.json` SHA-256: `edcae7ec97a518b703b94cfba4f1cc24ad7dc9dac21c299e9c40f586da941a4e`
- Raw result bytes: 5,747,447; audit bytes: 8,778.
- Formal output was generated on 2026-09-21 in the dedicated `formal-01` directory. Source/freeze are recorded in `FREEZE.json`; exact hypothesis, thresholds and stopping rules are in `PREREGISTRATION.md`.

## Interpretation / next step

The intervention is promising for shifted CORRECT recall but insufficiently reliable under the fixed gate. Do not promote this model or relax the threshold based on this run. A successor experiment could test a stronger or stratified CORRECT augmentation while holding the same paired-seed and false-CORRECT constraints; preregister it as a distinct issue and retain this failed result unchanged.
