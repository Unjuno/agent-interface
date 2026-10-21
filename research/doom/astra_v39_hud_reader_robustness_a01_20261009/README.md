# V39 HUD reader perturbation robustness A01

This is a CPU-only, post-transfer stress test of the current-main health glyph reader on the same 13 exact model-input frames used in the preceding cross-run transfer check. It asks whether small capture-to-window misregistration and common pixel transforms make the reader fail closed or report a wrong health value.

## H / T / D / C / U

- **H:** Across the 13 frozen frames, the current-main reader will never return an observed health value different from the frozen manual label after any preregistered perturbation. The conditions are eight whole-frame translations of 1 or 2 pixels with the original window binding held fixed, brightness and contrast factors 0.95 and 1.05, and JPEG recompression at qualities 95 and 75.
- **T:** Verify the current-main reader and all 13 source-frame hashes, reproduce exact baseline labels, apply each fixed transform in memory, and record reader status/value and transformed-pixel hashes. This yields 182 perturbed reads plus 13 unmodified positive controls.
- **D:** `PASS_NO_FALSE_OBSERVED_VALUE` requires 13/13 baseline matches and zero perturbed reads that report an observed value different from the frozen label. Unknowns count as fail-closed for this narrow property, while their frequency is reported separately. Any wrong observed value is a FAIL.
- **C:** These are deterministic image perturbations, not a sample of real capture faults. The exact-match WAD templates may reject harmless changes and still pass this no-false-value criterion.
- **U:** This test does not establish a false-positive probability, real-time capture robustness, latency, guard integration, threat response, release, task effect, survival, recovery, or MAP01 progress. The frames are sparse retained decision images, and every perturbation is synthetic.

## Observed result

The 13 unmodified frames matched the frozen health labels (13/13). Of the 182 perturbed reads, none returned a wrong observed value; 181 returned `unknown`, while one retained the correct value (health 11) after a one-pixel downward translation. The narrow no-false-value criterion passed. This reader is highly fail-closed under these transforms, with correspondingly low availability: every brightness, contrast, and JPEG variant returned `unknown` for all 13 frames. All eight translation variants also returned `unknown` for every frame except that one retained reading.

The first auditor (`audit.py`) returned `FAIL_AUDIT` because its parameter check omitted the candidate's JPEG-byte digest. That raw failure is retained in `results/audit.json`. A second auditor launch initially stopped on a missing `argparse` import; its hash and error are retained in `results/audit_v2_initial_failure.json`. The corrected posthoc audit (`audit_v2.py`) then passed all five mutation controls and independently recomputed the transform hashes and counts in `results/audit_v2.json`. Neither audit issue changed or reran the frozen candidate result.

## Reproduction

From the repository root, with the frozen WAD available:

```sh
python research/doom/astra_v39_hud_reader_robustness_a01_20261009/analyze.py --wad /path/to/freedoom2.wad
python research/doom/astra_v39_hud_reader_robustness_a01_20261009/audit_v2.py --wad /path/to/freedoom2.wad
```

The candidate was executed once for the frozen ID `v39-hud-reader-perturbation-a01-20261009`; the command is retained as the reproduction recipe, not permission to overwrite this result. It reads source blobs and frames from the frozen Git commit, so it works in a sparse checkout, and writes `results/a01.json`. The corrected posthoc auditor checks provenance, transformation coverage, transformed-pixel hashes, classification arithmetic, and five mutation controls and writes `results/audit_v2.json`. The WAD is only read and is not copied into this package. Preserve the initial auditor failures as evidence; do not relabel them as candidate failures or delete them.
