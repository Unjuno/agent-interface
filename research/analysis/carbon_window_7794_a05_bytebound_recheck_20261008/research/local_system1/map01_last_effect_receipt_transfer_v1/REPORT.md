# MAP01 last-effect receipt transfer — retained first outcome

Task `LOCAL-SYSTEM1-MAP01-LAST-EFFECT-RECEIPT-TRANSFER-20260917-001`, Issue #943.

## Disposition

**`PASS_LAST_EFFECT_RECEIPT_TRANSFER_SCOPED`**.

Container-only retained-evidence replay under `/tmp/ai_exp_last_effect_v30_20260917_001`. One source-first frozen formal invocation; reruns/replacements/tuning0. No GUI, game, model, provider, network task action, task input, authority grant, or shared-runtime mutation occurred.

## Frozen question

The predecessor representation used exact caller-visible prompt bytes. Change one factor only: append the final effect receipt from the immediately preceding retained decision projected to exactly `{action, extent, result}`, else `NONE`. No MAE, timestamps, image/pixels/hash, current/future state, evaluator state or free text enters the feature.

## First outcome

- eligible retained v30 rows: **3** (iterations 3/4/5);
- prompt-only collision groups: **1**;
- prompt-plus-last-effect collision groups: **0**;
- known decision3/4 prompt collision reproduced: **true**;
- their last-effect values are distinct: **true**.

The known pair uses the same prompt Git blob `2c3d84fa1a89f11243ecc82dc62edc41024f03ab`. Decision3 has `last_effect_receipt=NONE`; decision4 has `{action: strafe_left, extent: short, result: visible_change}`. Decision5 has `{action: turn_left, extent: pulse, result: visible_change}` and a different prompt.

All formal rows retain `authority=none` and `task_input=false`.

## Integrity

- frozen v30 report Git blob `e4525a236ebe12cf87d4466a6dd2e8dcd8ff7d24`, exact size 47,355 bytes;
- FORMAL_RESULT SHA-256 `37fbf3171f3f92c979efde0365e02cb5a4505a678d83191f9fecfee8d4bd018a`;
- independent AUDIT SHA-256 `1b0e9cd87182b617f89c35940c83a17bfa96a813761887bc6aa185118de7b618`, passed `true`, errors `[]`;
- CORRUPTION SHA-256 `d67492255f427f963033ff96012404cfd68338742cbeaa18a2fce903aefb84e5`, controls reject **5/5**;
- postformal scientific source hashes match the premeasurement freeze.

A postformal read-only display helper initially used the wrong key shape for `FREEZE.json` and raised `KeyError: ROADMAP.md`; no experiment source/result/audit/input was changed or rerun. Correct schema inspection then verified the frozen source hashes exactly.

`SOURCE_BUNDLE.json.gz.b64` decoded JSON SHA-256 `95e8de729b63ce8b1537ea59a1a9aa77d6dacb09873340370aed3a3046ea6311`. `EVIDENCE.json.gz.b64` decoded JSON SHA-256 `7a02817d8775967729b96be2698053b920adaa8c4c4d070df23b8a25cc98408b`. `reconstruct.py` verifies both identities and exact input Git blobs before extraction.

## Interpretation boundary

The single added caller-available feature makes this tiny retained v30 eligible set function-like for exact teacher-label imitation. It does not prove population sufficiency, unique action optimality, semantic task-effect equivalence, or that a learned backend is useful. The next rung should freeze the integrated representation and compare the smallest exact deterministic RULE/LINEAR/TREE tiers before allocating any learner.
