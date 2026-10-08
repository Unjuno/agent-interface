# UNPOSTED proposal: click-to-focus recovery with an occluded target

Suggested lineage: successor scope to #4036 / PR #4053, related closed #55 and #2789. This is a different native hit-target/side-effect condition explicitly outside #4036, not an extension of its denominator. Check live ownership before publication; do not invent an Issue number or re-execute the allocation.

This proposal records the already completed, locally preregistered `activation-hit-target-20260922-01`, not prospective public preregistration. Exact H/T/D/C/U is preserved in PLAN.md; first source freeze and all 26 native outcomes are included. Result: PASS_ACTIVATION_HIT_TARGET_BOUNDARY_SCOPED, confirming the bounded failure modes, not approving a universally safe candidate. CLICK_THEN_TYPE / POST_FOCUS / HIT_AND_FOCUS each have eight cases and produce 4/0/0 wrong-field texts and 4/4/2 unwanted Button callbacks respectively. All clear/unrelated-cover positives work; no task input in the two controls. See REPORT.md and AUDIT.json.

One same-app stacked Button can intercept a focus-recovery click without changing the registered Entry's XID/geometry. Post-click recipient evidence protects text but not the earlier callback. A fresh native hit check rejects preexisting occlusion but not later occlusion. No general GUI/model/cost/atomicity claim follows.

Current delivery is blocked locally by absent GitHub write capabilities. Keep that incident in this same evidence record. No shared code/earlier result/parallel branch was modified; no retries; no runtime promotion or global roadmap closure. This draft has NOT been posted.
