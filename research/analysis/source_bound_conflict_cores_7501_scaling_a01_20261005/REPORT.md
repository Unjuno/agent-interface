# Issue #7501 A01 — bounded all-MUS enumeration scaling

## Disposition

`PASS_SCALING_BOUNDARY` for the preregistered constructed family. The candidate and independent auditor each ran once; both exited 0. Six complete rows exactly matched the independent exhaustive oracle. Two budgeted rows stopped at 1,024 subset checks, reported `INCOMPLETE`, and denied dispatch. All four planned output mutations were rejected. Retries: 0.

## H / T / D / C / U

**H.** For `k` independent contradictory Boolean pairs, exact subset enumeration returns all `k` two-clause minimal cores after exactly `2^(2k)-1` checks when fully budgeted. With a lower explicit budget, it returns `INCOMPLETE`, never permits dispatch, and any returned partial cores remain unsatisfiable and deletion-minimal.

**T.** Eight deterministic cases (`k=1..6` fully budgeted; `k=7,8` budget 1,024). Each `x_i` has source-distinct relaxable clauses `x_i` and `!x_i`. Candidate checks subsets in cardinality-first order. The independent auditor uses assignment enumeration and integer-mask subset order. Both ran once inside WSLc 3.0.1.0, cached image `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364` (local repo digest `sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`), CPython 3.12.15 x86_64, with network disabled, read-only source bind mount, and separate writable output mount. Container IDs, commands, state, hashes, logs, and inspect records are in `RUN.json` and `formal_01/`.

| k | Clauses | Full subset count | Budget | Work | Result | Cores emitted |
|---:|---:|---:|---:|---:|---|---:|
| 1 | 2 | 3 | 3 | 3 | complete | 1 |
| 2 | 4 | 15 | 15 | 15 | complete | 2 |
| 3 | 6 | 63 | 63 | 63 | complete | 3 |
| 4 | 8 | 255 | 255 | 255 | complete | 4 |
| 5 | 10 | 1,023 | 1,023 | 1,023 | complete | 5 |
| 6 | 12 | 4,095 | 4,095 | 4,095 | complete | 6 |
| 7 | 14 | 16,383 | 1,024 | 1,024 | incomplete | 7 partial, individually valid |
| 8 | 16 | 65,535 | 1,024 | 1,024 | incomplete | 8 partial, individually valid |

**D.** `PASS_SCALING_BOUNDARY`: each completed row returned exactly its `k` expected MUSes with exactly `4^k-1` subset checks. Both budgeted rows remained incomplete/non-dispatchable at the exact budget. The independent audit matched every completed core set, checked every partial core for unsatisfiability and deletion-minimality, and rejected: dropped complete core, budgeted row promoted to complete, dispatch from incomplete, and work above budget.

**C.** This family is favorable and synthetic. Arbitrary CNF/MUS instances can have different core counts and substantially worse enumeration behavior. A safe incompleteness signal can also mean no complete explanation is available within an operational budget.

**U.** Finite Boolean enumeration only; no natural-language encoding, user comprehension, GUI/runtime authority, production dispatch, effect safety, or general SAT/MUS performance claim. CPU-only; no GPU, model, GUI, human participant, or external action. WSLc reported that swap limiting is unavailable and cgroup is not mounted; requested memory configuration is recorded but not claimed as enforced.

## Raw evidence and validation

- Candidate output and stdout: `formal_01/candidate.json`, `candidate.stdout.json`, `candidate.container.log`.
- Independent audit and stdout: `formal_01/audit.json`, `audit.stdout.json`, `auditor.container.log`.
- Exact container inspect: `formal_01/candidate.container.inspect.json`, `auditor.container.inspect.json`.
- `FREEZE.json` pins the main commit, source blobs, script/fixture SHA-256, image ID/digest, runtime, caps, and preflight states. Source hashes matched immediately before and after each formal invocation.
- Candidate/auditor syntax compilation passed before freeze. Source mounts were verified read-only and output mounts writable in the exact exited-container inspect records. Network mode was `none`; exit code was 0 for both.
- WSLc repeated the warning: `Your kernel does not support swap limit capabilities or the cgroup is not mounted.` No resource enforcement claim is made.
