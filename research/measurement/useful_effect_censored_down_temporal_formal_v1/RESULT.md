# Formal result — censored-down temporal gate v1

Decision: **PASS_CENSORED_DOWN_TEMPORAL_GATE_SCOPED**

Issue: #988  
BASE: `08876d8f332aabc6d63fa46d5d02a7f98c55c92f`  
Candidate SHA-256: `58ec7ac9f8f2115aceec42236f42e2cdbb298d2fd1a0f7824e096474a47edb0f`

Exactly one frozen formal invocation evaluated 100,000 fresh cases / 420,971 effect records with seed `98420260917002`. Reruns/replacements/tuning: 0.

Independent audit:
- candidate/oracle mismatches: 0;
- ambiguous -> bound promotions: 0;
- exact-down parent mismatches: 0;
- provenance precedence mismatches: 0;
- occupancy mismatches: 0;
- audit errors: `[]`.

The EXACT_DOWN stratum contains 25,000 cases and emitted zero `temporal_ambiguous`. The CENSORED_BOUNDARY stratum retained 45,029 ambiguous effect records instead of upgrading them to bound useful/non-useful evidence. Effect records did not mutate occupancy in any formal case. Fixed malformed controls passed 8/8.

Formal result SHA-256: `9fdea092f92e651a91f10fa35cb22991248e6528faaa84f5c3acdfd6b1e0e34f`.  
Audit SHA-256: `207225ffd4e0cf01f92dd1e05a9f3abdf12af7a94ce4a4116f7ca963a334ff4d`.  
Candidate-case digest: `26dd443fd253d59f3eeb8c8303bacfe7be589d92be3f164f450428d1cf7fd521`.

Postformal copied-result corruptions reject 3/3: seed, digest and invocation count. Source rehash after formal matches the frozen source SHA-256 values.

## Scope

Synthetic same-clock integer-time evidence only. This establishes that a censored physical press interval requires an explicit ambiguous temporal state before a bound useful-effect claim. It does not prove real X11 transition times, application consumption, semantic causation, MAP01 usefulness, human tempo, or production ABI behavior.
