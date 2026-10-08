# A02 retained screenshot grounding replay — experiment record

## H — hypothesis

The existing A01 procedure creates a 24×24 image-patch handle around a model-proposed control coordinate, then revalidates the exact patch in a fresh observation. When replayed against the retained A14 outputs, it should admit visible control points and refuse coordinates from an observation with no field or Save control.

The procedure under test is unchanged from A01. This experiment does not ask whether an image patch is semantically a field or button; it evaluates how the actual registry behaves on these retained coordinates.

## T — frozen test

- Input source: PR #7353 head `e8f7c02cb98d849312a4889fa4d52ec424088732`.
- Five 1280×800 PNGs and five model answer JSON blobs are pinned by Git blob ID and SHA-256 in `INPUTS.json`; the PNG bytes are copied into `inputs/`.
- Candidate coordinates are extracted from each retained `answer.json`.
- For each field and submit coordinate, mint a 24×24 `window_content` target handle, then resolve against the same pixels as observation sequence 2. Source and fresh observations use the same focus/surface/geometry binding. No input dispatch is available in the harness.
- The A14 visual review's task-3 “blank page” classification was the initial negative assumption. The exact pinned screenshot was visually inspected after the first candidate run and visibly contains the Value field and Save button. That source claim is recorded as contradicted in `VISUAL_REVIEW.json`; task 3 is not treated as a valid negative case.

## D — decision rule and outcome

The initial expected gate was 8/8 visible targets `VALID` plus 2/2 task-3 coordinates refused. The first substantive test failed both expectations: task 3 returns `VALID` for both controls, while field centers in tasks 4–6 are `FLAT_REFUSED`. Direct review confirms all ten saved points lie within visible form controls in the frozen screenshots. The input-label assumption was therefore invalid, and the initial red test is preserved rather than regraded as a target-absence failure.

The corrected descriptive outcome is 7 `VALID` and 3 `FLAT_REFUSED` across ten points, with zero model calls, GUI calls, input dispatches, or side effects. Each flat refusal occurs before any registry entry is created. This is a safe-stop / coverage limitation: the fixed center patches inside three visible text fields are visually flat, so the current texture gate refuses them. It is not evidence that these tasks were completed or that a handle is semantic target proof.

## C — interpretation limit

The exact-pixel match verifies only that a local patch remains at the same bound location. It does not establish that the patch is the requested semantic control. This retained sample contains no visually absent-target negative after the task-3 mismatch was reconciled, so false-positive grounding behavior on a textured distractor remains untested. The three field refusals also show that a 24×24 center patch can reject a visibly correct low-texture target; no threshold or region-size tuning is performed here.

The A14 narrative, original first-test failure, final raw results, screenshot hashes, and independent audit are retained separately. This is offline construction evidence only, not live GUI qualification, task-effect evidence, recovery evidence, or an efficiency result.

## U — unknowns

- Whether larger, target-aware crops can admit low-texture fields without admitting textured distractors.
- Whether any fresh observation-bound alias is semantically correct for a new target.
- Whether the live action-admission path consumes such aliases safely and verifies task effect.
- Whether any method improves #57 end-to-end correctness, latency, or cost.

## Reproduction

From the repository root:

```powershell
python research/integration/coordinate_grounding_gate_57_a01_20261004/a02-retained-screenshot-grounding/extract_frozen_inputs.py
python research/integration/coordinate_grounding_gate_57_a01_20261004/a02-retained-screenshot-grounding/run.py
python -m unittest discover -s research/integration/coordinate_grounding_gate_57_a01_20261004/a02-retained-screenshot-grounding -p test_candidate.py -v
python research/integration/coordinate_grounding_gate_57_a01_20261004/a02-retained-screenshot-grounding/audit.py
```
