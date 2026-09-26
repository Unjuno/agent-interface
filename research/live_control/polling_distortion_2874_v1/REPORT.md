# #2874 polling distortion first formal outcome

Decision: **HOLD_NO_MATERIAL_DISTORTION_EXPOSED**.

The fresh 152-case allocation completed exactly once: four routes × the exact #225 38-case schedule template. No predecessor row was pooled, and no formal route was rerun or replaced.

## Results

| route | target detections | nuisance false detections | cue-duration median | timed record-work median |
|---|---:|---:|---:|---:|
| RENDER_ONLY | n/a | n/a | 5.3152875 ms | 0 ms |
| FULL_10MS | 13/30 | 0/8 | 5.3510605 ms | 1.8802675 ms |
| FULL_2MS | 30/30 | 0/8 | 5.411943 ms | 1.6709565 ms |
| DEFERRED_RECORD_2MS | 30/30 | 0/8 | 5.391640 ms | 0.0631225 ms |

The canonical audit reconstructs 152 rows with errors=[] and decision HOLD_NO_MATERIAL_DISTORTION_EXPOSED. FULL_2MS cue-duration median exceeded RENDER_ONLY by only 0.0966555 ms; DEFERRED by 0.0763525 ms. The preregistered material-distortion threshold was 0.5 ms (10% of the nominal 5 ms cue), so the current host did not reproduce a material predecessor-style distortion. Consequently this allocation cannot causally attribute #225's larger draw-duration perturbation to per-acquisition packaging.

Evidence packaging work nevertheless changed sharply: FULL_2MS median timed record work 1.6709565 ms versus DEFERRED_RECORD_2MS 0.0631225 ms, while both fresh 2 ms routes had the same total detection count and zero nuisance false detections. That is a mechanism descriptor, not the preregistered causal PASS because the required material distortion was absent.

## Scope

Private Xvfb/Tk/XTEST/XGetImage known-colour ROI only; one Linux host, no CPU/frequency pinning or calibrated timing uncertainty. No model, game, user desktop, network experiment, arbitrary-GUI, hard-real-time or production claim.
