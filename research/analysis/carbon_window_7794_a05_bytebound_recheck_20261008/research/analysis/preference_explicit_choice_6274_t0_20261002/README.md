# Preference-explicit choice certificate — Issue #6274 T0

## H / T / D / C / U

- **H:** A requester-only latency rule can select an alternative that all explicitly ranked principals consider worse than another option, despite identical requester task effects. An authorization-first certificate can filter revoked grants and nontradeable constraints, preserve possible/certain Pareto frontiers under incomplete ordinal preferences, and leave nonunique choice to the explicitly delegated person.
- **T:** Five synthetic cases, three principals, four same-requester-effect routes, exhaustive enumeration of all weak-order completions, separate independent rank-vector oracle, four deliberately invalid mutation controls. No human preference, model, GUI, network, shared file, or real authorization is used.
- **D:** PASS_METHOD_SCOPED requires exact oracle agreement; quick-route dominance detection; partial profile possible frontier {conflict, quick, review} and certain frontier {conflict, quick}; revoked d_route and protected quick route excluded before ranking; explicit delegate chooses only their strict top; all-equal profile returns every route with no automatic choice; all four mutations rejected. Otherwise retain FAIL_AUDIT/FAIL_METHOD; no post-hoc repair of a formal result.
- **C:** A designated owner's explicit choice may be simpler; declared equal-weight Borda is only a named ordinal baseline, not a fairness guarantee. Synthetic rankings can make a Pareto frontier look more decisive than any real setting warrants.
- **U:** No actual person's satisfaction, preference elicitation, fairness, welfare, consent/legal status, live GUI safety, deployment, or product value follows. The method assumes the frozen candidate set, common requester effect, grants and protected constraints are correctly labeled.

## Pre-experiment correction incorporated

"Fast but Pareto-dominated" is only coherent when the requester explicitly ranks the slower dominator above the faster route. The fixture does so. Missing pairwise comparisons remain unconstrained; all valid weak-order completions (including an explicit tie completion) are enumerated. A revoked route is removed before preferences are projected to the eligible set. In the protected case, two of three principals rank the fastest route first, but its explicitly declared private-content violation for the third principal removes it before any ranking or majority baseline.

## Reproduction

fixture.json is the frozen input; candidate.py is the candidate and audit.py is a separately implemented raw-fixture auditor. The candidate writes results/formal-01/candidate.json; the auditor reads it and writes results/formal-01/audit.json. Exact source, fixture, image and command identities are in FREEZE.json; actual invocations, outputs, exit codes and hashes are in results/formal-01/RUN.json and SHA256SUMS.

Local construction gate: python3 -B -m unittest discover -s research/analysis/preference_explicit_choice_6274_t0_20261002 -p 'test_*.py' -v.

Formal gate: run the candidate once, then the independent auditor once, in pinned network-isolated Docker. Do not retry a formal candidate or relabel a failed audit.
