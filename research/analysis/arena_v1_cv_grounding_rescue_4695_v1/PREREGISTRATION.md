# Arena v1 local visual-refinement boundary — preregistration

Parent issue: [#4695](https://github.com/Unjuno/agent-interface/issues/4695)  
Allocation: `arena-v1-cv-grounding-rescue-4695-20260927-01`  
Branch: `research/arena-v1-cv-grounding-rescue-4695-20260927`  
Evidence path: `research/analysis/arena_v1_cv_grounding_rescue_4695_v1/`

## H — hypothesis

A deterministic local orange-square proposal extractor can replace a grossly out-of-frame Qwen pixel guess with a precise visual box when exactly one sufficiently large, square, high-fill orange connected component exists, while abstaining when the target is absent, non-square, or ambiguous. It is a proposal-only perception primitive, never click authority.

## T — bounded experiment

- Frozen candidate: RGB channel tolerance 8 around `(249,115,22)`; 4-connected components; area 1,600–12,000 pixels; width/height 0.84–1.19; fill ratio >=0.86; emit only when exactly one component passes.
- Twelve fixed 720x520 panels: the exact retained Arena image; five synthetic unique-target positive layouts with red/yellow square distractors and an orange-circle distractor; three absent-target controls (including orange circle and diamond); three multiple-orange-square ambiguity controls. The retained frame is hashed and included, not recreated. Synthetic source and all PNG bytes/hash bindings are included.
- Candidate consumes only PNG pixels. It receives no hidden labels or expected boxes. On the retained panel only, the original out-of-bounds Qwen point `[920,640]` is preserved in the raw row; local output remains a proposal with no action emission.
- Independent auditor imports neither candidate detector nor suite generator. It reads the PNGs and manifest, independently extracts threshold-connected boxes, verifies input hashes/denominator, compares positive IoU, and checks abstentions. Five copied-evidence corruption controls must reject.
- Run in the cached pinned helper image `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`, Python 3.12/Pillow, CPU only, `--network none`, `--pull=never`, read-only root/source/input, writable output/tmp only. No GUI, model/provider, network, clicks, native input, or user data.

## D — decision

`PASS_SCOPED_LOCAL_REFINEMENT` requires 6/6 unique-target positive IoU >=0.95, 6/6 absent/non-square/ambiguous abstentions, the retained `[920,640]` proposal explicitly shown out of bounds and locally replaced by the audited box, exact source/image/PNG hashes, and all five corruption controls rejected. Any positive localization miss is `FAIL_REFINEMENT_LOCALIZATION`; any control proposal is `FAIL_UNSAFE_FALSE_PROPOSAL`; identity/denominator/audit mismatch is `HOLD`; source/image/runtime unavailable is `STOP`. No input action is ever authorized by this experiment.

## C — confounders

This uses high-contrast synthetic panels and one retained public-generator frame. It directly encodes the orange RGB family and square geometry; semantic intent, target freshness/motion, occlusion, antialiasing variation, different themes, dynamic frame changes, action admission and effect verification are not tested. The color rule could overfit this one primitive.

## U — limits

No model quality, Arena task completion, B0/C1 comparison, real-app transfer, latency/efficiency benefit, semantic understanding, safe click authority, or product readiness claim. The #4695 broad paired benchmark remains open.

## Freeze integrity

This file, `generate_suite.py`, `refine.py`, `run_suite.py`, `audit.py`, `test_protocol.py`, and `corruption_test.py` are frozen before scored output. Suite manifest and 12 image SHA-256s are generated before the candidate is run. The exact Docker image ID, commands, source hashes, outcome JSON, independent audit and scope limits are retained with the result.
