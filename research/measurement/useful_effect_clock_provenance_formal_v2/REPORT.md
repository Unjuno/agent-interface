# Useful-effect clock provenance formal v2 — first outcome

Decision: **`PASS_USEFUL_EFFECT_CLOCK_PROVENANCE_FORMAL_SCOPED`**.

Exact merged #1004 candidate Git blob `b8e35581eaf1f99f6ad973f4bde1367e43eb0a1b` was held byte-for-byte. Formal seed `100420260917002`; exactly 180,000 fresh records:

- same clock: 50,000;
- cross domain: 35,000;
- cross epoch: 25,000;
- missing clock provenance: 25,000;
- precedence/unbound/unscored/malformed-effect mixtures: 45,000.

Results:
- candidate vs independently structured oracle: **180,000/180,000 exact**;
- same-clock degeneration to independently implemented #988 semantics: **0 mismatches**;
- cross-domain / cross-epoch / missing-clock scored known-lineage records promoted to `useful_bound` or `nonuseful_bound`: **0**;
- frozen boundary/malformed controls: **13/13 PASS**;
- model/network/task-input/authority actions and occupancy mutations: **0**.

The formal result contains 60,000 `temporal_clock_mismatch` and 25,000 `temporal_clock_unknown` classifications. Matching clock labels therefore preserve the parent temporal rule, while missing/mismatched provenance fails closed before bound useful/non-useful effect evidence.

Formal invocation: 1; reruns/replacements/tuning: 0. Independent audit passed all 12 checks with errors `[]`; five copied-result corruptions were all rejected.

Interpretation boundary: this validates the typed provenance admission rule only. Matching labels do not prove that two real clocks are actually synchronized/comparable; #1000/#1002 and future live telemetry own measured clock relation. No X11, application-consumption, MAP01-usefulness, human-tempo or production ABI claim follows.
