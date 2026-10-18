# A02 — duplicate epoch frame coherence

This synthetic source-level probe tests three V39 monitor boundaries against the exact source frozen from main e4db1a9115cdf4f9163bddc169a7313672b9155e:

- a different hash on a strictly newer sequence/capture epoch preserves the paired policy;
- an identical typed-to-observation duplicate for the same epoch preserves it;
- a different frame hash on a same-epoch cross-transport duplicate invalidates with signal_pair_duplicate_epoch_mismatch, requiring a new decision and granting no input authority.

A01's first harness error remains in its sibling directory and was not rerun. A02's candidate ran once. Its raw JSON accidentally embeds A01 as the experiment ID. AUDIT_INITIAL_UNBOUND.json preserves the initial auditor PASS, which failed to bind that identity. RESULT_POSTHOC.json changes only the experiment ID and records the raw-output hash; AUDIT_POSTHOC.json independently reconstructs the three cases and explicitly reports the raw identity deviation. The raw candidate output and initial audit remain unchanged.

This is construction evidence only. Hash change has no semantic threat interpretation. No game, model, GUI, OS input, physical release, active cover, useful feedback, task effect, recovery, survival, or live allocation was measured. Issue #59's live V39 threat-exposure gate remains open.
