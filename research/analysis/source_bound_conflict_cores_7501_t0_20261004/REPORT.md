# Issue #7501 T0 — executed finite conflict-core method result

## Disposition

`PASS_METHOD_SCOPED` for the preregistered nine-row, finite Boolean contract fixture. The one candidate and one independent auditor both exited 0; all eight planned output mutations were rejected. This does not validate natural-language interpretation, source authentication, GUI execution, or a production dispatch gate.

## H / T / D / C / U

**H.** For a small typed contract language with pre-authored clause meanings, complete enumeration of minimal conflict sets against declared hard constraints can distinguish SAT, conflict, and incomplete/unknown outcomes while refusing infeasible/unknown dispatch and never offering hard clauses for relaxation.

**T.** Candidate and auditor each ran once in separate OrbStack containers from exact main `fe5a9dddf11f0351eb65001f1a1ddb867e8a5012`; image ID `sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80`, Node `v26.10.0`, arm64. The engine was Docker 29.4.0 on cgroup v2. Both runs used network `none`, read-only rootfs, 1 CPU, requested 512 MiB memory / 512 MiB memory+swap (zero swap by Docker's configuration convention), PID limit 16, UID 501, and one writable package bind mount. Both exited 0 with OOM false. Engine warning: `DOCKER_INSECURE_NO_IPTABLES_RAW is set`. Requested memory/swap values are configuration evidence only; this run did not independently read the containers' live cgroup memory/swap files, and claims no measured resource-enforcement guarantee.

**D. PASS_METHOD_SCOPED.** Candidate and assignment-first exhaustive oracle agree on all nine rows. Counts: `SAT=1`, `CONFLICT_CORE_COMPLETE=3`, `BLOCKED_BY_HARD_CONSTRAINT=1`, `UNKNOWN=1`, `INVALID_PROVENANCE=1`, `STALE_REVISION=1`, `INCOMPLETE=1`. The three-clause unsat fixture returned its single three-member minimal core. The overlapping fixture returned both minimal cores `[u1,u2]` and `[u1,u3]`, excluding irrelevant `u4`. The bounded search stopped at one work unit and reported INCOMPLETE, not SAT. No row dispatched except the one SAT contract-gate fixture. The auditor independently confirmed each emitted core was unsatisfiable and deletion-minimal, and rejected all eight mutations: dropped core member, irrelevant member added, second MUS omitted, UNKNOWN promoted, incomplete marked complete/SAT, hard clause offered for relaxation, stale revision reused, and dispatch added to infeasible/unknown rows.

**C.** A generic typed negative result plus a human-authored restatement may be simpler and sufficient. Minimal cores may add computational cost or false precision without improving the user's next decision; apparent UNSAT may instead reflect omitted variables or alternatives.

**U.** This tests stipulated Boolean formulas and synthetic source-span identifiers, not authenticated source provenance, faithful natural-language compilation, user comprehension, open-world GUI behavior, solver scale, real effectful dispatch, or task success. `dispatch_allowed` in the candidate is only a simulated contract-feasibility gate, not runtime authority. The SAT row does not establish permission to act. No runtime code changed.

## Invocation and retained artifacts

- Candidate: 1 invocation, exit 0; raw result [candidate.json](formal_01/candidate.json), stdout [candidate.stdout.json](formal_01/candidate.stdout.json).
- Independent audit: 1 invocation, exit 0; raw result [audit.json](formal_01/audit.json), stdout [audit.stdout.json](formal_01/audit.stdout.json).
- Retries: 0. No game, model, GUI, external action, or human participant.
- Preflight `node --check` for both frozen scripts and fixture JSON shape check passed. A Node image/runtime smoke check passed before freeze; it is not counted as a candidate or auditor invocation.
- All frozen source hashes matched on post-run check; see `FREEZE.md`. Output SHA-256: `candidate.json` `a53fc2808b9245e598e0965d2f3dc97117b7f1e413e1374fad2f2dc429a9670c`; `candidate.stdout.json` `e520c6c5df6065b955ef7d6246d087b93330b78ad58337803d03b45ab7ec1c87`; `audit.json` and `audit.stdout.json` `4a6446208d1a5d10f00b34017653c687593e388d803ec23b2f82545e1c6bcde8`.
- No additional failure or STOP occurred. The daemon warning and absence of direct cgroup-file observation are retained above as environment/scope limitations, not hidden or interpreted as method failures.

## Next boundary

If continuing this Issue, first establish authenticated source-span/revision binding and an immutable hard-background presence requirement, then test whether a source-linked all-MUS explanation helps a human-authorized restatement without automatically ranking or relaxing clauses. This method PASS alone does not justify runtime integration.
