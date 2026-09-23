# Semantic MVCC read-set v1 — Result

Issue #4257. Allocation `semantic-mvcc-readset-4257-20260923-01`.

## Result

**PASS_SEMANTIC_MVCC_READSET_SCOPED**.

One formal invocation over 10 frozen cases. No reruns, replacements, exclusions or tuning.

- STRICT_SNAPSHOT accepts: 1/10
- READ_SET_VALIDATE accepts: 3/10
- correct late results salvaged relative to strict snapshot: 2
- false accepts: 0
- independent raw-only audit: 120 checks, errors=[]
- copied-evidence controls: 12/12 rejected
- authority grants: 0
- formal raw SHA-256: `d17e4cfd32cdb90ed796f936a0e2b3e143f584d5cf18170c7ad35324fdef3831`

The two salvaged cases changed only an irrelevant toolbar field/global observation generation. Target change, dialog change, dependency UNKNOWN, intent change, producer-generation change, target ABA restoration under a new dependency generation, and late completion were all rejected. Exact value restoration did not restore applicability identity.

Validation timing is descriptive only: STRICT_SNAPSHOT median 189 ns/max 1,074 ns; READ_SET_VALIDATE median 692 ns/max 2,556 ns in this provided container. These are not performance gates and do not estimate real-model break-even.

## H/T/D/C/U

- H: complete authored dependency read sets can salvage some in-flight semantic results after unrelated state change while rejecting relevant/generation/deadline changes.
- T: deterministic standard-library fixture, 10 frozen cases, semantic read set `{target, dialog}` plus intent version, producer generation, observer epoch and decision deadline. Provided Linux x86_64 execution container / CPython 3.13.5.
- D: 2 preregistered irrelevant-change results salvaged, zero false commits, every negative control rejected, raw audit and 12 mutations pass.
- C: read-set completeness is assumed by fixture; #4233 remains the unresolved completeness boundary. Integer schedule times are semantics, not timing measurements.
- U: no model preprocessing dependency completeness, GUI/task transfer, token savings, production latency, authority or product claim.

## Retained execution-envelope incident

The formal study child, frozen auditor and corruption-controls child each returned exit 0 and produced complete retained files. After those outputs, the outer container tool wrapper reported status 1 and included `TERM environment variable not set`. This is retained separately in `formal/OUTER_TOOL_INCIDENT.json`. The scientific allocation was not rerun.

## Integration meaning

This supports an optimistic-validation boundary for semantic proposals only under complete declared dependencies. A late semantic result may remain usable when irrelevant global state changed, but a committed semantic result is still not action authority. Hidden/undeclared dependencies remain a fail-closed problem, as separately exposed by #4233.
