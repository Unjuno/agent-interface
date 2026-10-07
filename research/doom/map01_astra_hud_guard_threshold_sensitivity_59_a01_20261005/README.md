# A01 — retained Astra HUD guard threshold sensitivity

## H / T / D / C / U

**H:** On the retained `map01-astra-attempt-v1` decision-frame sequence, the previously selected health HUD ROI may remain sensitive to threshold changes over a bounded range, while the face-animation control ROI may spuriously invalidate a policy. This is a posthoc robustness check, not an estimate of live error rates.

**T:** Freeze current-main source commit `406431f5790ca2e8a8888bcfe1e82730432d8b49`, the retained 13-frame manifest, health transcription from the existing failure analysis, two existing ROIs, RGB thresholds `{16,32,64}`, and changed-pixel cutoffs `{25,100,250}`. Replay each adjacent frame pair through the production one-way guard; independently recompute changed-pixel counts from the raw images.

**D:** Method-scoped pass if all 18 cells reconcile to an independent pixel-level implementation and source frame hashes; descriptive robustness is limited to the grid. No claim about prospective thresholds, continuous false-negative rates, semantic threat detection, or task benefit.

**C:** Manually transcribed HUD labels, one failed run, adjacent decision frames only, static ROI geometry, animation and unrelated scene changes; no independent live capture stream.

**U:** Twelve intervals cannot estimate operational sensitivity/specificity. Posthoc choice and fixed ROI may exaggerate separation. Pixel change does not identify semantic direction, prove a threat, or show policy appropriateness.

## Executed command and result

On Windows CPython 3.11 with Pillow, from repository root:

```powershell
python research/doom/map01_astra_hud_guard_threshold_sensitivity_59_a01_20261005/run_candidate.py
python research/doom/map01_astra_hud_guard_threshold_sensitivity_59_a01_20261005/audit_independent.py
```

The candidate reports 7/7 annotated health changes with 0 false invalidations at RGB thresholds 16 or 32 for all three changed-pixel cutoffs. At threshold 64/cutoff 250 it misses 2/7. The face control invalidates 6–12 of 12 intervals labeled unchanged-health across the tested grid. Independent pixel replay passes all 18 cells and verifies all 13 source-frame hashes.

## Disposition

`PASS_METHOD_SCOPED` for deterministic reconstruction and threshold-grid reconciliation. This is a posthoc analysis of one retained failed run; it does not establish a suitable operational guard, live threat response, causal survival benefit, bounded recovery, useful feedback, or MAP01 exit. The face control demonstrates that raw ROI change is not sufficient as a semantic policy invalidation trigger. Keep the existing live threat-exposure gate open.
