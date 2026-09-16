# Effect compensation collateral invariant v1

Task `EFFECT-COMPENSATION-COLLATERAL-20260916-001`, Issue #468.
Publication base: `d25aee1bdda23b757735990ab22e027e21cf0e18`.
Premeasurement source/plan freeze: `4364ead0d3bc6f553dbd357d629cc86680a778f3`.

Decision: **`PASS_COLLATERAL_COMPENSATION_BOUNDARY_SCOPED`**.

## Question

The preceding retained result established that a compensating effect may restore the current primary state without erasing the historical wrong effect. This rung changed exactly one factor: whether compensation verification checks only that primary value or the full declared invariant including one preserved collateral property.

## Frozen experiment

A cooperative local SQLite effect owner stores authoritative `(primary, collateral)` state and an append-only ordered event history. Initial state is `(old, preserve)` and intended direct state is `(target, preserve)`.

Thirty fresh formal first outcomes were frozen before measurement: ten each for:

- `correct`: direct effect -> `(target, preserve)`;
- `wrong_compensated_clean`: wrong effect -> `(wrong, preserve)`, then compensation -> `(old, preserve)`;
- `wrong_compensated_collateral`: wrong effect -> `(wrong, preserve)`, then compensation -> `(old, damaged)`.

The two labels differ only in compensation-verification scope. `primary_only` declares compensation verified when the primary value returns to `old`; `full_invariant` requires both primary and collateral to return to the declared invariant. Both retain the historical wrong effect and compensation events.

Sources, tests and the exact 30-case plan were published before the first formal case. Prefreeze `unittest` passed 4/4. GitHub readback blob identities matched the locally executed receiver, experiment, auditor, tests and plan.

## First formal outcome

All 30 formal IDs completed exactly once; same-ID reruns were zero.

| Scenario | n | Final state | primary_only | Full invariant |
|---|---:|---|---|---|
| correct | 10 | `(target, preserve)` | 10/10 `EFFECT_VERIFIED` | 10/10 `EFFECT_VERIFIED` |
| wrong + clean compensation | 10 | `(old, preserve)` | 10/10 `EFFECT_CONTRADICTED_COMPENSATED` | 10/10 `EFFECT_CONTRADICTED_COMPENSATED` |
| wrong + collateral damage | 10 | `(old, damaged)` | **10/10 falsely `EFFECT_CONTRADICTED_COMPENSATED`** | 10/10 `EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE` |

Total truth agreement is **20/30** for primary-only verification and **30/30** for full-declared-invariant verification.

The result is deliberately narrow: restoring the target value is not sufficient evidence that compensation restored the task state when another required invariant was changed. This does not imply that the experiment can discover all relevant collateral state automatically.

## Independent audit and corruption controls

The independent auditor imports neither experiment classifier nor receiver implementation. It reads each retained SQLite database, checks event ordering and final state against the last event, independently recomputes both labels, and reconciles published rows. It passes all 30 formal cases with no errors.

Four posthoc controls were performed on copies only; no formal evidence was modified. The auditor rejected all four:

1. flip one retained primary-only label;
2. corrupt one SQLite collateral state;
3. delete one retained compensation event;
4. duplicate a formal plan ID.

These controls are validation of the auditor, not additional formal trials.

## Evidence retention

The lossless formal bundle is 8,229 bytes compressed, SHA-256 `b4cfe9ad8416039573916b0afd0ddba2778b86c6e108f3504bc4240c77e8cf54`, containing all 30 SQLite databases, all 30 row JSON files, full formal result, audit, summary, frozen plan and freeze record.

GitHub retains the archive losslessly as seven exact base64 chunks plus `reconstruct.py`. The seven Git blob identities are recorded in `EVIDENCE.json`; local reconstruction from those same canonical chunks passed the archive SHA check and extraction.

An initial monolithic base64 publication attempt was detected as truncated by GitHub readback and deleted before this PR. The formal measurement was **not** rerun or changed; only the publication transport was repaired.

## Environment and limits

Measured locally with CPython 3.13.5, SQLite 3.46.1, Linux 6.18.44 / glibc 2.41, Intel Xeon Platinum 8272CL, visible CPU affinity 0..4. No timing or throughput claim is made.

This is a cooperative local SQLite fixture with an authored scalar collateral invariant. It does not establish automatic dependency discovery, generic undo, arbitrary external-service compensation, GUI semantics, network/distributed transaction correctness, concurrency, power-loss behavior, natural failure rates, or production API stability.

## Architectural implication

For any future typed outcome contract, `compensation_verified` must be evidence relative to the **declared required post-compensation invariant**, not a single primary field. Historical `effect_occurred` must remain separate regardless of whether restoration later succeeds.

The next construction step should therefore extend the typed outcome reducer from #464 to accept an explicit set of independently verified required invariants, while refusing to label compensation complete if any required invariant is missing or contradicted. That integration should remain model-free and additive before any shared-runtime promotion.
