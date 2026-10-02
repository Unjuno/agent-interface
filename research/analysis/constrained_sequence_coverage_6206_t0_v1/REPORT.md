# Constrained event-sequence coverage T0

**Disposition: `PASS_METHOD_SCOPED`.** In this finite synthetic reducer, the 33-trace shortest-witness ordered-adjacent-pair suite covered all 33 feasible adjacent event-type pairs and detected the planted `REV→ACT` stale-lease mutant that the 48-trace static event-presence suite missed. The 33-trace seeded random comparator also detected that mutant in this draw, so the result does not establish superiority over random testing. The 135-trace length-3 suite detected the planted `OBS→REV→ACT` mutant, while the ordered-pair suite did not. Independent raw-only audit: 14/14 checks, including exhaustive enumeration and four corruption controls.

| Frozen suite | Traces | Scoped observation |
|---|---:|---|
| Exhaustive legal schedules, lengths 0–4 | 863 | Reference denominator; 1,555 total words enumerated |
| Static event-presence subsets | 48 | Complete for all 59 feasible presence-level pair tuples; order-blind; missed `REV→ACT` mutant |
| Seed-6206 random schedules, matched budget | 33 | Detected `REV→ACT` in this single seeded draw; not a statistical comparison |
| Shortest-witness ordered-adjacent-pair suite | 33 | Covered all 33 feasible adjacent pairs; detected `REV→ACT` with witness `[REV, ACT]` |
| All feasible length-3 schedules | 135 | Detected `OBS→REV→ACT`; pair suite did not |

The exhaustive legal set has 35 feasible relative-order pairs and 178 feasible relative-order triples; those denominators are distinct from the 33 feasible adjacent pairs. The two impossible release examples were rejected, and removing `PING` preserved the modeled state and non-PING outputs. The initial length-2-only construction was found incomplete before formal execution (26 direct pairs versus 33 feasible adjacent pairs); the preregistered correction chose shortest legal witness traces and was recorded on Issue #6206 before candidate/auditor invocation. That history is preserved; the final package does not claim a minimum set-cover suite.

## Execution and evidence

The frozen candidate was invoked once and the separately authored independent auditor once, both with exit code 0; retries and substitutions were zero. Formal execution used Python 3.14.5 on macOS arm64, standard library only. No container, model, network, GUI, game, or user input was used. The unrelated active shared Docker container remained untouched. Construction tests passed 4/4 before freeze. Candidate and audit outputs are retained byte-for-byte; their SHA-256 values and exact run identities are in [RUN.json](RUN.json) and [SHA256SUMS](SHA256SUMS).

This result validates only the frozen length≤4 synthetic transition model, chosen suites, two planted mutants, and the independent audit. It does not establish that ordered coverage generally outperforms static/random/exhaustive testing, nor any real runtime, hidden GUI state, timing/concurrency, task-effect, safety, reliability, or cross-domain claim. Main advanced after source freeze by a disjoint runtime-only commit; source and formal results were not rebased or retuned. PR integration and hosted checks remain separate gates.
