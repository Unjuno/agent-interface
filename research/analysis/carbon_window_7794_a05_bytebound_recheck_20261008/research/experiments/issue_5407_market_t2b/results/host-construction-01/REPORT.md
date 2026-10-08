# Issue 5407 T2b — capacity-aware reallocation host construction

Allocation: `issue5407-market-t2b-capacity-reallocation-20261001-02`  
Base branch snapshot: `c3227bccfbb7f95ff950edb0d86888ed26f99ece`  
Branch: `research/5407-capacity-aware-reallocation-t2b-20261001`

## Result

**Disposition: `FAIL_HYPOTHESIS_SCARCITY_FIRST_WORSE_ON_FIXED_MATRIX`; raw audit: PASS.**

The preregistered scarcity-first policy had **187 less safe admitted value** than value-first, with the same zero unsafe admissions. Its safe shortfall was 187 higher. Scarcity-first cost stayed within the frozen 125% budget, but its coverage criterion failed.

| Policy | Admitted | Unsafe admissions | Safe admitted value | Safe shortfall value | Selected cost |
|---|---:|---:|---:|---:|---:|
| Scalar unconstrained | 250 | 236 | 179 | 672 | 2,687 |
| Value-first constrained | 153 | 0 | 1,981 | 2,064 | 1,970 |
| Scarcity-first constrained | 162 | 0 | 1,794 | 2,251 | 2,296 |
| Exact safe-value oracle | 173 | 0 | 2,162 | 1,883 | 2,361 |

Across this fixed synthetic workload, the scalar policy assigned all 250 available two-agent slots but 236 pairings violated task authority, evidence, or high-risk failure-domain constraints. Both constrained policies enforced those constraints. Scarcity-first admitted nine more tasks than value-first but selected lower-value tasks at the expense of 187 aggregate value. The oracle establishes an upper bound for this finite assignment problem; it is not an implementable scheduler.

## H / T / D / C / U

- **H:** scarcity-first constrained tuple assignment would lower safe unserved task value versus value-first, at zero inadmissible admissions.
- **T:** one frozen 50-seed matrix, 8 tasks and 10 single-capacity heterogeneous agents per seed; scalar, value-first, scarcity-first and exact safe-value oracle were evaluated on identical inputs. Raw decision traces include workload, bid costs, assignments and metrics.
- **D:** hypothesis **FAIL** on its primary comparison: scarcity-first shortfall 2,251 vs value-first 2,064. Safety and cost conditions passed: both constrained policies had zero unsafe admissions and scarcity-first cost 2,296 was 116.5% of value-first cost 1,970. The independent raw-only audit checked all 50 seeds, reconstructed all metrics, verified oracle optimality and returned zero errors. Its unsafe-role-alias and reused-agent mutations were rejected.
- **C:** the scarcity-first heuristic may preserve scarce pairs yet spend capacity on lower-value tasks. Value-first may remain preferable when global assignment feasibility is low. The exact oracle is a comparator only.
- **U:** deterministic synthetic inputs omit deadlines, task DAGs, strategic bidding, non-stationary costs, false evidence, and real agents. No truthfulness, real-world fairness, production, GUI-safety, or user-benefit claim follows.

## Reproduction and provenance

Host-only commands (no Docker/OrbStack, GPU, model, network, GUI, or input):

```text
python -m py_compile work/5407_market_t2.py work/5407_market_t2_audit.py
python work/5407_market_t2.py --seed-start 0 --seed-count 50 --tasks 8 --agents 10 --out work/5407_market_t2.jsonl
python work/5407_market_t2_audit.py work/5407_market_t2.jsonl
```

The raw-only auditor emitted `audit=PASS`, `rows=50`, `errors=[]`. Exact original raw SHA-256: `402f53e118c3bf0dd92187eed5d4eb35476519dad4c4a622e26c77894a78e5fd` (391,635 bytes). Python: CPython 3.11.9 on Windows. The current-main observation immediately before source freeze was `42ded9d35204583655d3524acedbe0ddd9357d1c`; the simulator consumes no project source files, and the preregistered source branch remains bound to its recorded base above.

Frozen source SHA-256:
- runner: `39ed31072bc0734a6d7a5fc3de5d5a9bd8626ee6d2ca5d795ededfe1418a521d`
- auditor: `b3a04fd65188a4a731056fddfb8b2c51709650256b78f79807a0b33e654c1d34`

This is a host construction result, not the preregistered network-disabled CPU-container reproduction. That separate rung remains unrun pending a fresh exclusive CPU allocation; no prior STOP or allocation was reused.
