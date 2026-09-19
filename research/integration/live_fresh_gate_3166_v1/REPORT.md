# Live two-tier fresh-gate experiment

Issue: #3166, successor to #2302/#1835.

## H/T/D/C/U

- H: a two-tier policy requiring prepared target evidence plus a fresh target gate refuses a replaced target; dependency-only admits the stale prepared target and is an unsafe reduced-policy witness.
- T: in fresh Docker, start two real GTK/X11 fixtures, prepare old XID 2097155, replace it with XID 4194307, then compare TWO_TIER_FRESH_GATE and DEPENDENCY_ONLY while retaining admission, runtime status, emission, effect, and release evidence.
- D: agent-interface-2994:20260920, digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c, --network none, Xvfb :151, model/network calls 0.
- C: PASS_LIVE_TWO_TIER_FRESH_GATE_SCOPED. TWO_TIER rejected both stale-old and lineage-mismatched replacement candidates before emission. DEPENDENCY_ONLY admitted the stale old target; runtime then failed focus verification with zero emissions and no effect. The physical fail-safe does not erase the unsafe admission witness.
- U: one GTK/X11 replacement topology. The result does not claim universal GUI safety, model behavior, or valid post-replacement action usability; #3170 supplies the distinct replacement control.

The raw X protocol error from the destroyed old window is retained as runtime evidence, not relabeled as a successful effect.
