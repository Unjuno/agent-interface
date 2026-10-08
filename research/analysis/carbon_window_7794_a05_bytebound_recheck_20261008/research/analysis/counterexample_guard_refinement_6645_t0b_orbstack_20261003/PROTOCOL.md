# Issue #6645 T0-B preregistration

Allocation: `CGREF-6645-T0B-ORB-20261003-02`  
Predecessor: A01 `STOP_PRE_FORMAL` before formal candidate/auditor invocation.  
Base: `c33380b3b08792a331ee11f7aee05e3d41437e3e`  
Runtime: OrbStack Docker, Linux/arm64, Python 3.12.14 from the exact local image digest.

## H / T / D / C / U

**H.** In this closed finite fixture, counterexample-qualified refinement over an explicitly complete observable vocabulary will refuse held-out harmful skill admissions while retaining an ordinary valid control, invalidating all siblings that depend on changed guard predicates, and returning UNKNOWN/fallback for untrusted, out-of-envelope, or observationally ambiguous cases. It should improve on unchanged-guard, invalidate-all, and exact-state-blacklist policies on the preregistered joint outcome, without claiming that a finite corpus is complete for real skills.

**T.** One skill has two cached specializations sharing a predicate dependency and one specialization with an independent dependency. Enumerate the frozen 10-case fixture. Train only on a replay-authenticated real guard miss; include a spurious/oracle-corrupt case, an irrelevant and an out-of-scope case, a valid rare control, a hidden-family/out-of-envelope state, three held-out harmful families, an observationally ambiguous safe/harmful pair, and fallback-present/absent controls. Candidate returns a canonically ordered set of all equally minimal guard refinements; it must not select among incomparable minima using hidden oracle labels. The independent auditor reconstructs every outcome from fixture truth, checks all state rows and cache dependencies, and verifies mutation rejection. No task input, GUI, model, network, external effect, or runtime cache is used.

**D.** `PASS_METHOD_SCOPED` only if: (1) only the independently replay-authenticated real miss refines; (2) candidate refinements are all minimum-cardinality options over the frozen vocabulary and ambiguity is preserved; (3) all three held-out harmful families are refused; (4) valid common remains admitted, while an observationally indistinguishable rare valid case may only become UNKNOWN; (5) hidden-family/out-of-envelope, corrupt, stale, and no-fallback cases fail closed; (6) both shared-predicate siblings invalidate and the independent sibling remains valid; (7) fallback adds no authority and no task input is replayed; (8) independent audit has zero errors and all frozen mutations are rejected. Any false admission is `FAIL_METHOD`; incomplete lineage/coverage is `HOLD`.

**C.** Conservative invalidate-all may be safer and simpler; exact-state blacklisting may fail held-out states; a predicate conjunction can overfit; an authored oracle can encode its own answer; #5504 shows omission of hidden predicate families can produce false passes. Accordingly the declared coverage envelope is mandatory and any unmodeled family maps to UNKNOWN.

**U.** Only authored finite states, labels, dependency graph, and predicate vocabulary. No natural state distribution, independent human oracle, automatic production guard repair, GUI semantics, security, latency/token benefit, or completeness outside the declared envelope is tested.

## Frozen execution and stop rules

Construction tests run first in the pinned local Python image with `--network none`, one CPU, read-only root, no capabilities, and a writable output mount only. Then run candidate once and auditor once in separate containers. No retries, tuning, formal reruns, or overwriting. A nonzero exit, OOM, missing artifact, oracle/auditor disagreement, or changed frozen source stops the allocation; preserve outputs as STOP/FAIL without relabeling. Container resource settings are not treated as proof of enforced memory limits.

Primary comparison metrics: false admissions among held-out harmful cases; valid-control retention; fail-closed UNKNOWN count; complete sibling invalidations; forbidden transitions. There are no timing or performance claims.
