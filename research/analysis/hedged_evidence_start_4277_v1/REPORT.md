# Hedged evidence start v1 — Result

Issue #4277. Allocation `hedged-evidence-start-4277-20260923-01`.

## Result

**PASS_HEDGED_EVIDENCE_START_SCOPED**.

One formal invocation over 9 frozen cases × 3 policies = 27 rows. No reruns, replacements, exclusions or tuning.

Frozen weighted endpoints:
- SEQUENTIAL_VOI: cost 3.764705882352941; latency 4.705882352941177; deadline miss 0.23529411764705882; wrong0.
- HEDGED_AFTER_AMBIG: cost 5.235294117647059; latency 3.823529411764706; deadline miss0; wrong0.
- ALL_PARALLEL: cost 7.705882352941177; latency 3.176470588235294; deadline miss0; wrong0.

Thus hedging removes the frozen sequential deadline misses while lowering weighted started-source cost by 2.470588235294118 (32.06%) versus ALL_PARALLEL. It costs more than SEQUENTIAL_VOI; the retained result is a deadline/cost frontier, not universal dominance.

Hard-infeasible source starts are0 for every policy. HEDGED records three late ignored results; ALL_PARALLEL seven. Ignored results remain non-authoritative, including the shifted conflict case where MEDIUM returns A first and later EXPENSIVE returns B.

Independent frozen audit: 236 checks, errors=[]. Formal raw SHA-256: `822fc3f64dc1edcd773ebcf92cbeac42f91eb1999fbd031fa74d02e41f2dbbeb`.

Frozen controls wrapper rejected 11/12 mutations and exited1. The sole non-rejection (`late_authority`) is retained as a harness no-op: it targeted row24's terminal MEDIUM event, whose `authoritative` value was already true. The preregistered gate is >=10 coherent evidence mutations, so the 11 effective frozen mutations satisfy it. A separately labelled postformal effective mutation changes an actually ignored late EXPENSIVE event on row25 to authoritative; the unchanged frozen auditor rejects it. No formal rerun or frozen-audit rewrite occurred.

## H/T/D/C/U

- H: CHEAP-first plus ambiguity-triggered MEDIUM+EXPENSIVE hedging can reduce deadline misses versus sequential selection without paying ALL_PARALLEL cost on cheap-decisive cases.
- T: deterministic standard-library event scheduler with full start cost, fixed source latencies/costs and nine weighted cases. No actual parallel thread/process benchmark.
- D: semantic/YIELD oracle preserved by all policies; infeasible starts0; HEDGED miss rate0 < SEQUENTIAL 0.2353 and equals ALL_PARALLEL0; HEDGED weighted cost5.2353 < ALL_PARALLEL7.7059; audit errors=[]; 11 effective frozen mutations reject plus one retained no-op control.
- C: authored table and fixed full start cost; no partial-cancellation/shared-provider economics. Source costs/latencies may favor the policy.
- U: no real model/provider, tokens, actual concurrency, GUI/task, authority or production claim.

## Integrity and lineage

#4263's prior PASS remains unchanged and is not pooled. This successor tests only its retained parallel-start competing explanation on a fresh evaluation table.

Preformal exact source/gate archive was published and Git-blob read back before formal. Construction 7/7 and py_compile are excluded. The first formal allocation is retained exactly once.
