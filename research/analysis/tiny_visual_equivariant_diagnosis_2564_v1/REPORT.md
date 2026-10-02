# Successor #4814 diagnostic: optimization vs receptive-field/pooling alias

Status: `STOP_DIAGNOSTIC_COMPLETE_NO_FORMAL_RUN`. This construction-only diagnosis does not validate a new model or revisit the frozen #4814 formal allocation.

## H/T/D/C/U

- **H:** The #4814 CNN failed because its 250-step optimizer was insufficient. Alternative: its 3x3 receptive field and global max pooling erase the patch extent needed to distinguish 9x9 positives from 5x5 distractors.
- **T:** On construction seed 8964300, check the 45 CNN derivatives by finite differences, sweep step/LR on a balanced five-position task, then vary only negative patch size.
- **D:** Construction seed 8964300; training initialization seed 8964305 in the LR/step sweep and 8964307 in geometry sensitivity. No formal seeds, held-out claim, or model efficacy inference. The intended geometry comparison retains 80 positives/80 negatives, same positive support, same training seed/noise, and fixed 1,000 steps at LR .2.
- **C:** Pinned local Docker image `sha256:ba509e8a38d311c07539c49a7a2970b6f19869de42b8008be07a85568e2c9824`; Python 3.11.2, NumPy 1.24.2; CPU only, one CPU, 2GiB, network disabled.
- **U:** If 5x5 distractors cannot be learned and no construction competence is achieved within 300s, stop without formal evaluation. Only a separately frozen successor may test a revised receptive-field/pooling design.

## Results

1. Finite differences passed for all 45 scalar values: kernel 36, channel bias 4, pooled dense 4, output bias 1; max symmetric relative error `6.68e-8`.
2. Balanced 5x5-distractor task did not become competent under any tested schedule:

| Steps | LR | fit seconds | train accuracy | train mean p(+/-) | base accuracy | heldout positive ACCEPT |
|---:|---:|---:|---:|---:|---:|---:|
| 250 | .80 | 3.25 | .5375 | .5006 / .5003 | .5375 | 0/320 per pooled eight positions |
| 1,000 | .20 | 12.51 | .5375 | ~.5006 / ~.5003 | .5375 | 0/320 |
| 2,000 | .05 | 25.40 | .5125 | ~.5002 / ~.5002 | .50 | 0/320 |
| 4,000 | .01 | 54.46 | .50 | .5002 / .5002 | .50 | 0/320 |

3. Balanced construction geometry sensitivity (same positive support and paired seed; one fit per condition, 1,000 steps/LR .2):

| Negative distractor | fit seconds | training accuracy | positive mean p | negative mean p | positive ACCEPT |
|---:|---:|---:|---:|---:|---:|
| 5x5 | 14.06 | .575 | .500077 | .500025 | 0/80 |
| 3x3 | 13.77 | .61875 | .502899 | .500960 | 0/80 |
| 1x1 | 12.14 | 1.00 | .999547 | .001549 | 80/80 |

All fits stayed under the 300-second diagnostic ceiling. This is one construction seed, and the geometry sensitivity uses training accuracy only; it does not establish generalization or efficacy.

## Interpretation

The evidence contradicts the simple “just train longer” explanation: four step/LR schedules, including 4,000 steps, remained at chance on the original 5x5-distractor task. The 1x1 control became perfectly separable in 1,000 steps, while 3x3 and 5x5 did not. This strongly implicates task/architecture interaction: a 3x3 local detector followed by global max pooling retains the strongest local match but discards extent, and the 5x5 distractor contains local regions similar to those in a 9x9 positive. However, the paired training fits use a single seed and do not prove this is the sole cause; initialization, optimization path, and finite model capacity remain possible contributors.

Therefore #4814 is evidence against this exact 4-filter/3x3/global-max design under the frozen synthetic task, not a general counterexample to translation-shared CNNs. No model is adopted; no confirmatory formal test is justified until a changed pooling/receptive-field design passes a newly frozen construction competence gate.

## Integrity notes

- #4814's raw formal output, initial audit HOLD, and corrected audit remain unchanged.
- An earlier geometry diagnostic accidentally used positive-only labels; its output is retained at `work/diagnosis_tiny_visual_equivariant_4817_v3/DIAGNOSIS.json` but explicitly invalid for balanced-class inference. The corrected class-balanced result is the v4 file whose digest is below.
- Some early protocol invocations stopped on ordinary import/scalar-index mistakes before any scientific fit; the final frozen source files below passed the recorded construction run.
- No external API, GPU, GUI, host action, or model service used.

## Artifact digests

- balanced LR/step sweep (`v2/DIAGNOSIS.json`): `367772d87c75b836aaec7b8f8c4e763a028b4984551eb8a597d2468a796af22c`
- corrected balanced geometry sensitivity (`v4/DIAGNOSIS.json`): `2d702d12fa252a98e7a5b462d378282ca92fd6b53cfa5f27378e00873a1a361d`
- finite-difference result (`GRADIENT.json`): `83e254bb23fa51fcb4b7b6b284c0ed5389a70bad3e57931293c24fe7feec4909`
- source SHA-256: `diagnose.py` `6e1c963d2d5225393c3b6f2d24c2b3bbb5676c08a04db40bfee4217ff8add576`; `gradient_check.py` `1c0dc0bc2ea59398f3ad5caa5c6f76e64600ed9f75b525f3f61fbd563f31643a`; `models.py` `89ab06367e7c98b86fc3e81128cf73baf9e41ed9519667b8ca623f712150d03e`; `prepare.py` `8bb24c96ff85310b2402d19b8f5d095154f36942dfc2d6178f14571f2529e424`.

Next experiment, if pursued, should retain 9x9 positives and 5x5 negatives but use an extent-sensitive pooling/readout (e.g. global mean plus max or explicit multi-scale features). Keep the new architecture and its seeds separate; construction competence must be demonstrated before formal seeds are allocated.

