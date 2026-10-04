# MAP01 engine-action feedback posthoc A01

This posthoc reconstruction joins per-key `d` admission and verified owner-thread key-up receipts to the independent scorer's sampled `Button.MOVE_RIGHT` state in all six retained cells of `absolute_pair_59_4d74_20261004`.

## H / T / D / C / U

- **H:** The retained pulse cells contain enough identity and monotonic-clock evidence to bound when the game last-action API first reports `MOVE_RIGHT` after each `d` admission, and when it first reports neutral after verified key-up.
- **T:** Read only the six frozen cells' runtime events, scorer last-action samples, and result summaries. Join admissions to verified releases by intent token/key and program/step; use the scorer button-name vector to locate `Button.MOVE_RIGHT`; derive observation brackets without interpolating between samples. Independently recompute from raw bytes and reject mutations.
- **D:** PASS for a fully sampled engine-action response only if each pulse admission has one verified same-step up receipt and coherent false→true→false samples, coast cells have no admissions/right-move action, and post-control scores remain present. HOLD if the finite scorer window censors a post-release neutral sample; never fill the gap by interpolation.
- **C:** Samples of the engine's last-action API may reflect simulation-tick polling and do not equal a physical event timestamp. `MOVE_RIGHT` is an engine-level action response, not a useful task effect or causal attribution to the key by itself.
- **U:** No MAP01 kill, health change, useful feedback, threat response, bounded recovery benefit, matched efficacy, or MAP01 exit is established. The original run was not repeated.

## Reproduction

From the repository root, run:

```powershell
python research/doom/v39_engine_action_feedback_posthoc_a01_20261005/analyze.py
python research/doom/v39_engine_action_feedback_posthoc_a01_20261005/audit.py
python -m unittest discover -s research/doom/v39_engine_action_feedback_posthoc_a01_20261005 -v
```

`FREEZE.json` pins every raw input and game-key configuration to source commit `c99d93a2c81945f0946173e48247bdd49e32a02a` by Git blob and SHA-256. The report uses scorer-call brackets as observation intervals; it does not claim the exact simulation tick at which the action changed.

## Current result

The single retained A02 pulse cell has two `d` holds. Both report `MOVE_RIGHT` before verified owner key-up; first-positive scorer-call brackets are 6.239–31.979 ms after admission across all six pulse holds. Five of the six holds have a first neutral sample 15.000–45.586 ms after the release-call return. For the remaining hold, the last scorer sample was right-move at 1.019 ms before the release call returned; the scorer window ended 11.060 ms after release, with no post-release sample. That is **HOLD_OFFSET_FEEDBACK_CENSORED**, not evidence that the action persisted after release.

All three coast cells have no input admissions or `MOVE_RIGHT` samples. All six post-control scores report zero kills and no MAP01 exit. The engine action API verifies that the pulse reached game action state; it does not show a positive task effect.
