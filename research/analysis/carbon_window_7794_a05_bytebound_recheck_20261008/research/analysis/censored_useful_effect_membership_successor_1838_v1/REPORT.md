# Censored useful-effect membership successor (#1964)

Decision: PASS_CENSORED_USEFUL_EFFECT_MEMBERSHIP_SCOPED

H: With censored integer DOWN/UP intervals, classify an ACTION effect as ALL, ANY, or FALSE according to every feasible world, rather than treating a point event as proof of continuous occupancy.

T/D:
- Exhaustive finite corpus over interval endpoints 0..6, effect -1..7 or absent, ACTION/ENVIRONMENT cause.
- 13,160 rows; candidate and independently structured oracle mismatch 0.
- Exact-edge cases agree with the oracle; nonzero ANY cases retained.
- Inward interval refinement never reverses a known ALL/FALSE verdict.
- Six tamper controls (verdict, missing, duplicate, endpoint, total, digest) detected.
- formal=1, audit=1, reruns=0, tuning=0.
- Candidate source is standard-library only; no model/provider/GUI/X11/network/task input.

C/U:
This is synthetic finite same-clock semantics. It does not establish live clock comparability, physical truth, causal usefulness discovery, occupancy duration, control efficacy, or human-tempo equivalence. The half-open occupancy convention and interval independence are explicit assumptions. Stop after this formal/audit; any live receipt-schema test needs a fresh successor.

Additive path only: research/analysis/censored_useful_effect_membership_successor_1838_v1/**
