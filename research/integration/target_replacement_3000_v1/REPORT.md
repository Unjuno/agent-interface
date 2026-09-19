# Distinct target replacement experiment

Issue: #3000

## H/T/D/C/U

- H: a replaced target with a distinct X11 identity is refused before input emission, while a live replacement control remains usable.
- T: in one fresh Docker allocation, start two concurrent real GTK fixtures under Xvfb; retain both XIDs; terminate the original; dispatch once against the old XID and once against the live replacement XID through the runtime CLI/X11 backend.
- D: agent-interface-2994:20260920, digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c, --network none, Xvfb :149, model/network calls 0.
- C: PASS_TARGET_REPLACEMENT_DISTINCT_SCOPED. Old XID 2097155 and replacement XID 4194307 were distinct. Old-target dispatch failed at focus verification with zero program emissions and verified empty release. Replacement control completed with four emissions, effect receipt, and verified empty release.
- U: one GTK/X11 topology only. This does not establish cross-platform identity semantics, arbitrary-window authenticity, or broad desktop correctness. The result tests runtime target replacement behavior, not the O3 evaluator's source-window binding contract.

The raw pre-fix and source-binding results remain unchanged. The experiment and runner are added additively.
