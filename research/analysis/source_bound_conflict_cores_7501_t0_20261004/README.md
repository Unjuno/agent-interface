# Issue #7501 T0 — source-bound minimal conflict cores

Status: frozen deterministic method experiment; formal candidate and independent-auditor invocations are each capped at one. No GUI, model, human participant, or effectful runtime path is involved.

## H / T / D / C / U

**H.** For a finite typed contract language with faithfully pre-authored clauses, complete enumeration of minimal conflict sets against an immutable hard-constraint background can distinguish feasible, infeasible, and unknown contracts more informatively than a generic conflict outcome, without dispatching on UNSAT/UNKNOWN or offering hard clauses for relaxation.

**T.** Nine deterministic CNF fixtures cover SAT; pairwise and three-clause conflicts; two overlapping MUSes plus an irrelevant clause; a hard authority conflict; unknown/unparseable input; duplicate source spans; stale contract revision; and deterministic search-budget exhaustion. Run the exact candidate and the separately implemented exhaustive assignment-first auditor once each in a network-disabled, read-only-rootfs OrbStack container. The only writable mount is this additive package path. No effectful dispatch occurs; `dispatch_allowed` is a simulated contract gate only. The auditor also tests eight output mutations.

**D. PASS_METHOD_SCOPED** only if the candidate matches exhaustive truth and all-minimal-core enumeration for every complete fixture; every core is UNSAT and deletion-minimal; both overlapping cores are returned; budget exhaustion is INCOMPLETE; unknown, stale, duplicate-provenance, and hard-conflict rows cannot dispatch; no hard clause is offered for relaxation; and the independent auditor rejects all eight mutations. Any mismatch is retained as the first FAIL/HOLD; candidate or auditor is not rerun.

**C.** Typed negative outcomes with an authenticated human restatement may be sufficient; a MUS may add cost or false precision without improving the next decision. Apparent UNSAT may also mean the finite task model omitted variables or alternatives.

**U.** Clause meanings and finite Boolean domains are stipulated. This does not validate natural-language parsing, source-span authentication, human comprehension, open-world GUI state, solver scaling, task success, or runtime safety. A complete MUS list is complete only for these finite formulas; it neither ranks repair choices nor authorizes relaxing a constraint.

## Freeze and execution

See `FREEZE.md` for exact source/image identities, resource settings, command lines, run caps, and stop conditions. The checked-out base is main `fe5a9dddf11f0351eb65001f1a1ddb867e8a5012`. This work occupies a detached local worktree and a unique additive path; no remote branch, PR, or existing Issue result is modified.

`formal_01/` retains candidate output/stdout and independent audit output/stdout. The first result governs. Development syntax/fixture-shape checks are not formal candidate/auditor invocations.
