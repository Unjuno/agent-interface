# Issue #7462 T0 result: `PASS_METHOD_SCOPED`

## Question and scope

Does bounded equality saturation find a lower declared-cost represented
program than fixed-order strict-improvement greedy while preserving every
stipulated observable contract in this finite DSL? This is a source-level
method experiment over authored ASCII transforms and a stipulated finite
transition/effect oracle. It is not a production e-graph, GUI/runtime,
human/model, or general optimizer result.

## Result

The frozen candidate saturated the complete declared rewrite closure for all
three programs (5, 4, and 10 terms; 3, 3, and 4 rounds respectively), without
reaching a cap. On the held-out freshness/effect-barrier program, extracted
cost was `(24, 11)` versus greedy `(25, 12)`, a strict improvement under the
frozen lexicographic cost. Independent exhaustive audit passed 324
state/effect comparisons. The `remove_refresh`, `reorder_edit_save`, and
`drop_release` mutations were each rejected, with 18 counterexample traces per
mutation. Audit errors: none.

Training results: the pure bridge extracted `(5, 4)` versus greedy `(6, 5)`;
the passive-check example extracted `(13, 7)`, equal to greedy `(13, 7)`.
The held-out gain is exactly one declared cost unit and one costly primitive;
it is not evidence of a material runtime speedup.

## Interpretation and limits

This supports only the frozen finite method claim. Equivalence depends on the
stipulated semantics (including ASCII-only trim/lower and identical passive
checks), authored fixture coverage, and chosen cost vector. Saturation here is
explicit finite whole-program equality closure, not a production union-find
e-graph. There is no empirical GUI, model, user outcome, performance, or
transfer evidence. The method may lose or be unnecessary under different
rewrite sets, costs, or program distributions.

Host-only standard-library Python was used; container isolation was not tested.
The earlier OrbStack cached-layer read STOP is recorded in `FREEZE.json` and
was not retried. Pre-freeze construction output is preserved but excluded.

## Reproduction

See `FREEZE.json`, `RUN.json`, `SHA256SUMS`, and `formal_01/`. From this
directory, after verifying the frozen source commit and hashes:

```sh
python3 -B -m unittest -v test_contract.py
python3 candidate.py --out formal_01/raw.json
python3 auditor.py --raw formal_01/raw.json --out formal_01/audit.json
```

The commands above describe the recorded sequence; do not rerun the one-shot
formal candidate or auditor allocation when reproducing this historical result.
