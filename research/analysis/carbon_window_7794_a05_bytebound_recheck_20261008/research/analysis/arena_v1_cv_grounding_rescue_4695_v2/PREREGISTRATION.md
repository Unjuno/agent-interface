# Arena v1 CV grounding rescue — successor v2 preregistration

Parent issue: #4750 (successor to #4695). Immutable v1 HOLD: PR #4743 / main commit `def11b4da6a27a57537aafa9812374c3fcd6aa39`.

## H — hypothesis

The v1 auditor conflated expected input structure with candidate output. An independent oracle that checks them separately will accept true multi-square ambiguity while rejecting false proposals, localization misses, identity/denominator changes, and altered input hashes. The unchanged v1 detector will also be tested on new held-out visual arrangements to estimate its narrow color/shape rule outside exact v1 fixtures.

## T — fixed protocol

- Candidate is byte-identical to v1 `refine.py`, expected SHA-256 `d243d5febfbbbc8eccf5f707caa81435cfb3cb8a1200c6f38bbbc770c56e3da1`; no tuning or retries.
- Regression cohort: the exact 12 v1 PNGs and manifest from `arena_v1_cv_grounding_rescue_4695_v1/inputs/`, verified by their frozen SHA-256 values. Their earlier predictions are not reused; the frozen detector is rerun unchanged.
- Held-out cohort: 12 deterministic 720x520 PNGs from `generate_heldout.py`, fixed seed 4695027: four single-square positives spanning the frozen area limits and canvas positions; four absent/non-square controls; four layouts containing 2–4 eligible orange squares. The generator, labels, expected boxes, manifest and every PNG hash must be committed before scoring.
- Independent audit implements its own connected-component extraction and imports neither candidate detector nor generator. For ambiguous rows it requires >=2 eligible input components and an ABSTAIN output; for absent/nonsquare, zero eligible components and ABSTAIN; for positives, exactly one eligible component, PROPOSAL, and IoU >=0.95. It checks identity, denominator, image hashes, retained out-of-bounds source point, and candidate-count/output consistency.
- Mutation suite must reject: wrong positive box, proposal on absent, proposal on ambiguous, missing row, duplicate/reordered identity, and altered input binding.
- Local Docker only, pinned helper `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`, CPU-only, no network, read-only source/inputs, output-only writable. No model/provider, GPU, GUI, clicks, native input, or user data.

## D — decisions

- `PASS_AUDIT_REPAIR_ONLY`: v1 rows satisfy corrected input/output oracle and every mutation is rejected. This resolves only the auditor inconsistency.
- `PASS_SCOPED_HELDOUT`: additionally all 4/4 new positives meet IoU >=0.95, all 8/8 new controls abstain, with exact hashes/identity.
- `FAIL_LOCALIZATION`: any positive fails the threshold.
- `FAIL_UNSAFE_PROPOSAL`: any absent, nonsquare or ambiguous control receives a proposal.
- `HOLD`: hash, identity, denominator, oracle independence, or mutation gate is not demonstrated.
- `STOP`: pinned local runtime or inputs are unavailable.

No outcome authorizes actions or runtime integration. Report regression and held-out cohorts separately. Any post-freeze source/gate change requires a new allocation.

## C — confounds

High-contrast synthetic panels and one retained frame are not representative of desktop visual distributions. The detector is explicitly orange-color/square-specific; held-out panels test only scale and placement diversity, not semantic grounding, themes, animation, occlusion, latency or action safety. Synthetic generation may create an easier distribution than real applications.

## U — integration

Keep outputs and sources under the v2 evidence directory; do not modify v1. Only a PR may integrate this reusable research evidence. A passing result remains proposal-only and requires separate real-app validation before any runtime use.
