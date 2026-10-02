# T11 — numeric derivation of approximate gluing status

## H / T / D / C / U

**H.** Deriving the minimum worst-case local residual from numeric relations, rather than accepting a supplied spread/status label, distinguishes exact, within-tolerance approximate, inconsistent, and incomplete evidence in this bounded model. Admission then applies the typed T10 contract only to a numerically derived approximate section.

**T.** Three variables range over the fixed eighth-unit grid `{0,2,4,6,8}`. Exact, near-inconsistent, larger-inconsistent, and missing-context cycles were evaluated at four tolerances, three contracts, and three action classes. The candidate exhaustively enumerates all 125 assignments for each input; the independent raw-only auditor reconstructs the minimax and policy result using `Fraction` arithmetic.

**D.** PASS scoped iff all 144 frozen rows match the independent oracle, exact/near/far minimax values are 0/2/4 ticks, below-minimax tolerances reject, incomplete evidence remains UNKNOWN and non-admitting, T10 admission boundaries hold, and all six non-identity mutations are rejected.

**C.** This is a tiny finite graph with a fixed quarter-grid and additive residual semantics. It does not model observation authority or a shared clock.

**U.** No real sensor/UI calibration, uncertainty distribution, general sheaf solver, freshness/provenance, causal ordering, authority precedence, GUI/model/task effect, runtime safety, or product claim follows.

## Frozen execution and result

- Allocation: `gluing-numeric-tolerance-5537-t11-20261001-01`.
- Freeze commit: `356e4f020`; base: `014069dc712d6c3f2f9805e64d16dbe943f9d09b`.
- Environment: CPython 3.14.5, Darwin arm64, host-only. No exact Docker/OrbStack lease was assigned to this branch; the shared lane was not borrowed. This finite CPU-only run used no GUI, model, network, input, or external effect.
- Construction, before freeze: `python3 -m unittest -v test_candidate.py` — 4/4 pass; 144 generated matrix rows matched the independent `Fraction` oracle; all six non-identity mutations rejected. `py_compile` and `git diff --check` passed.
- Formal candidate: one invocation of `python3 -B run_experiment.py`, exit 0; 144 rows, four cases, four tolerances, three contracts, three actions. Raw SHA-256: `0047d900c903f661980bb5ffc8e81377ae1498042a1ab041d7cea74003907a11`.
- Independent audit: one invocation of `python3 -B audit_raw.py`, exit 0; `base_errors=[]`; six of six mutations were non-identity and rejected. Audit SHA-256: `a211bd46eb0964177c02e784b97215386faf4b7d9ee27b6e12f777ee2ad3830a`.

| Case | Minimum worst-case residual | Derived status by tolerance |
|---|---:|---|
| exact cycle | 0 ticks | global section certified at all tolerances |
| near cycle | 2 ticks (1/4) | no global section at 0/1; approximate section at 2/4 |
| far cycle | 4 ticks (1/2) | no global section at 0/1/2; approximate section at 4 |
| missing context | 0 on the known subgraph | UNKNOWN at every tolerance; never admitted |

The exact case admits under all three contracts because its section is exact. For approximate sections, `exact_only` admits none; `reversible_approximate` admits reversible/compensable actions only; the explicit opt-in contract additionally admits irreversible actions, and only at or above the derived minimax tolerance. Total admitted rows: 51/144 (36 exact, 10 near, 5 far; 0 missing-context).

## Raw artifacts and frozen source hashes

- `raw/formal.jsonl` — SHA-256 `0047d900c903f661980bb5ffc8e81377ae1498042a1ab041d7cea74003907a11`
- `raw/audit.json` — SHA-256 `a211bd46eb0964177c02e784b97215386faf4b7d9ee27b6e12f777ee2ad3830a`
- Frozen source hashes and exact command protocol: [`FREEZE.json`](FREEZE.json).

The one-shot result and audit are retained as executed. This is not evidence that numeric tolerances are calibrated or that approximate gluing should authorize real interface actions.
