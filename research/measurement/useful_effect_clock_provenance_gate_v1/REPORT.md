# Useful-effect clock provenance gate v1

Task: `USEFUL-EFFECT-CLOCK-PROVENANCE-GATE-20260917-001`

Decision: **PASS_USEFUL_EFFECT_CLOCK_PROVENANCE_GATE_SCOPED**.

Construction-only standard-library evidence. The candidate preserves the #988-style non-temporal gate order and changes only the scored+bound temporal comparison: effect and actuation must expose the same nonblank `{clock_domain, clock_epoch}` before numeric timestamp ordering is allowed.

First construction outcome:
- fixed controls: 12/12 PASS;
- same-clock #988 parent degeneration: 84/84 exact;
- seeded random mixed records: 425,000;
- candidate/oracle mismatches: 0;
- same-clock parent mismatches: 0;
- numeric-only cross-clock records incorrectly promoted to `useful_bound`/`nonuseful_bound`: 8,189;
- clock-bound cross-clock promotions: 0;
- malformed dataset controls: 3/3 reject;
- authority grants / task-input calls / occupancy mutations: 0 / 0 / 0;
- random-corpus digest: `7130134fabf2abe36a71692d056502e4c1a81da4f669ebcf36000b46aeae38e3`.

Independent audit: PASS, errors `[]`. RESULT SHA-256 `2d42ae329ef83e59cac49ca66907b819e3854e07b4daec06b82b77483f17f8cf`.

Interpretation: a numerically ordered effect timestamp is not sufficient evidence for the #988 temporal gate when the effect and actuation clocks are not explicitly comparable. Missing or mismatched clock provenance must remain unknown/mismatched rather than being promoted to bound useful-effect evidence.

Scope is synthetic same-process integer-time semantics only. Matching clock labels do not prove synchronization, causation, application consumption, or live X11/MAP01 usefulness. #1000 separately studies same-host cross-process clock comparability; #998/#999 remain untouched.
