# Result — Issue #59 generic OCR post-hoc probe

Execution-history qualification: see [EXECUTION_HISTORY.md](EXECUTION_HISTORY.md).
The retained RESULT is the final of three packaged runs after an informal
matrix run; earlier full raw/timing outputs were overwritten. It is not a
one-shot or independent replication. Original hash-bound source files and
the final RESULT remain unchanged.

**Outcome:** `POSTHOC_EXPLORATORY_INDEPENDENT_OCR_GATE_NOT_ESTABLISHED`.

Tesseract 5.5.2 was run 168 times over 14 retained frames where the source
typed health value changed. Each frame was cropped to the fixed 78×38 HUD box,
enlarged 10× with nearest-neighbor, and processed under a fixed 3×4 matrix.
The best *single fixed configuration* matched 4/14 recorded typed values
(grayscale, PSM 8 or PSM 13). Picking the best configuration separately for
each frame after seeing all outputs matched 5/14 (sequences 62, 103, 115, 167,
193); this per-frame oracle is optimistic and not an operational score. All
eight threshold/inverted-threshold configurations matched 0/14.

This is a negative exploratory result for the tested generic OCR baseline, not
evidence that no independent reader can work. The labels are from the same
run's WAD-specific typed extractor, the test was post-hoc, the sampled frame
pair had already been inspected, and the same matrix was run informally once
before this package was frozen. The packaged run preserves full outputs; it is
not an independent replication. No independent human-labeled set exists.
Therefore exact accuracy against truth, independent useful-feedback onset,
causal interpretation of health loss, controller benefit, and recovery
efficacy remain unmeasured. The Issue #59 live gate remains open; this does not
authorize or replace its separately gated prospective allocation.

An exploratory follow-up using Apple's Vision OCR was **stopped before any
image was processed**: `swift --version` required prior Xcode license
acceptance, while bundled and Homebrew Python both lacked the `Vision` module.
No license acceptance, installation, or privileged change was attempted. A
Linux OrbStack container would not supply Apple's macOS Vision framework.
Exact diagnostics and the stop boundary are retained in `STOP_VISION.md`.

The complete per-frame raw OCR outputs, elapsed times, source and PNG hashes,
and RGB-digest checks are in `RESULT.json`. `audit.py` independently
reconstructs the transition selection, validates every input/frame identity
and timestamp, and recomputes the agreement counts. Its PASS is an artifact
integrity result only, not a semantic OCR pass.

The container-first option was checked and stopped without mutation:
`orbctl status` reported `Running`, but the `orbstack` Docker context could not
read the existing `python:3.12-slim` image because a containerd blob open failed
with `operation not supported`. No pull, build, VM operation, reset, or other
worker's container was touched. The exact diagnostic is in `STOP_ORBSTACK.md`;
the portable CPU-only Tesseract audit therefore ran on the local host.

## Local verification

On the captured environment, the package's four `unittest` tests passed,
`py_compile` passed for all three Python files, and the independent artifact
audit passed all three checks. No live game, model, input, or allocation was
used.
