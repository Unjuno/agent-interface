# Issue #4449 — positive-cycle rule retraction (current-main execution)

This is a fresh execution record for the #4449 finite hypothesis on current
main. The earlier reservation `research/cyclic-rule-retraction-20260926-u4r1`
and its intake commit remain unchanged. No runtime code is modified here.

## H / T / D / C / U

**H** — For a finite, complete positive OR-of-AND dependency graph, deleting
one rule while roots remain fixed cannot add grounded claims. Clearing the
deleted head's surviving dependency cone and rederiving only inside it reaches
the same least grounded set as a full rebuild. Descending local-support pruning
can falsely retain an unsupported positive cycle; clearing without rederiving
can falsely remove an alternatively-supported claim.

**T** — Exhaust all 64 masks of six fixed rules over roots E0,E1 and claims
A,B. For each mask, include one no-change row and one row for every active-rule
deletion: 64 + 6*32 = 256 rows. Compare an affected-cone clear/rederive
candidate and a full rebuild with an independent least-model oracle; also
measure the two named counterexample policies. Run in the pinned local OrbStack
Python image, network disabled, read-only study source, read-only root, bounded
CPU/memory/PIDs, and a dedicated result mount. No GUI, model, provider, user
data, native input, seed, or experiment network.

**D** — PASS requires exactly 256 source-bound rows; candidate and full rebuild
equal the independent oracle on every row; no deletion adds grounded claims;
claims outside the affected cone are unchanged; no-change rows preserve the
original result; local-support false-retains at least one cycle; blind
invalidation false-removes at least one alternatively-supported claim; the
raw-only audit has zero errors; and all 10 evidence-corruption controls reject.
Any complete semantic contradiction is FAIL. Missing integrity is STOP/HOLD.

**C** — The rule graph is declared complete, positive and fixed; both roots
remain active; exactly one existing rule may be removed. The model makes no
claim about hidden supports, rule insertion, changing roots, negation,
concurrency, authenticity, timing, or production resource ownership.

**U** — Exhaustive only for this two-claim/six-rule finite graph. No runtime,
GUI/task, performance, model utility, production-adoption or general arbitrary
graph claim follows. The independent oracle is a separate implementation, not
external human review.

## Roadmap

Construction subset in OrbStack -> freeze/read back current-main source and
inputs -> one 256-row formal invocation -> raw-only oracle audit and 10
corruption controls -> local applicable CI -> evidence-only PR -> exact-head
checks/review -> merge and main readback if qualified.

See `PLAN.md`, `FREEZE.json`, and `RESULT.md` for executable identities and
the retained outcome.
