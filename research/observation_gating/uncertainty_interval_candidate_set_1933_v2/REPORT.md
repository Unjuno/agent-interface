# Calibrated near-tie candidate-set result — Issue #4276

## Decision

**PASS_INTERVAL_AMBIGUITY_SET_SCOPED**

One prospectively source/gate-frozen formal invocation, 64 rows, reruns/replacements/tuning 0/0/0.

| category | rows | candidate true-max retained | point TOP1 true-max retained | candidate dominated inclusions |
|---|---:|---:|---:|---:|
| CLEAR_SINGLETON | 16 | 16/16 | 16/16 | 0 |
| NEAR_TIE_POINT_WRONG | 24 | 24/24 | 0/24 | 0 |
| OVERLAP_MULTI | 12 | 12/12 | diagnostic only | 0 |
| EXACT_TIE_COMPATIBILITY | 12 | 12/12 | diagnostic only | 0 |
| all | 64 | 64/64 | — | 0 |

Independent raw-only audit: `errors=[]`. Candidate reconstruction 64/64. Authority grants 0. Coherent copied-evidence controls rejected 12/12. Postformal contract tests re-pass 5/5. Formal/audit/control exits are all 0; formal/audit/control stderr are empty.

## Contract theorem

For region `i`, let the latent dimensionless score satisfy `L_i <= z_i <= U_i`. Let `m = max_j L_j` and candidate set `C = {i | U_i >= m}`.

1. **No feasible latent maximizer is omitted.** If `t` is a latent maximizer then `z_t >= z_j >= L_j` for every `j`, so `z_t >= m`. Since `U_t >= z_t`, `U_t >= m`, hence `t in C`.
2. **Every certainly dominated region is excluded.** If `U_i < m`, choose `j` with `L_j=m`. Then `z_i <= U_i < L_j <= z_j`, so `i` cannot be a latent maximizer.

The formal experiment validates the frozen implementation/evidence boundary of this interval rule; it does not empirically calibrate the intervals.

## Frozen variables

| symbol | meaning | SI unit | definition | domain / assumption | type |
|---|---|---|---|---|---|
| `s_i` | detector point score | 1 | frozen integer estimate | finite integer | scalar |
| `e_i` | uncertainty radius | 1 | frozen nonnegative integer | `e_i >= 0` | scalar |
| `L_i,U_i` | interval endpoints | 1 | `s_i-e_i`, `s_i+e_i` | `L_i <= U_i` | scalar pair |
| `z_i` | scorer-only latent score | 1 | frozen fixture oracle | `L_i <= z_i <= U_i` | scalar |
| `m` | largest lower bound | 1 | `max_j L_j` | four regions | scalar |
| `C` | possible-max set | 1 | `{i | U_i >= m}` | subset of four IDs | finite set |
| `N` | formal rows | 1 | 64 | exact | integer |

Dimensional check: all score quantities are dimensionless, so subtraction and ordering are dimensionally valid; no timing or physical-unit threshold participates in PASS/FAIL.

## Provenance / first-outcome integrity

- intake main: `c79f70a93d603748b155449016581dd7b9aac205`
- allocation: `uncertainty-interval-candidate-set-1933-v2-20260923-01`
- corpus SHA-256: `39ad89ed5924429011d1988fa5ed5386c8c1b6b5b6352546e0b59719274a305e`
- preformal source capsule SHA-256: `a6dbfbce0b20613a1df318e4bd5c284d777a8de4fbac57ef3f17a6fe8e029ef0`
- formal result SHA-256: `fdd67b59016b1ed921fb059bd61319f3ac6424c1e56008c1e45953e36d8133bc`
- audit SHA-256: `c2b50732429618e863d55efbb553f9f0445180a7bbca37d0ddc4e148a6595814`
- controls SHA-256: `34f15333c3c57d478dbdfe415733d1dd953d0500160425061a4eab9bcbc06037`
- formal invocation/reruns/replacements/tuning: `1/0/0/0`

Construction packaging STOP and the preformal Base64 trailing-LF publication correction remain retained in `CONSTRUCTION.md` and the Issue comment; neither changed the decoded frozen source/corpus or formal gates.

## Scope

This is a finite integrity result for authored/calibrated score intervals. It does **not** establish how a real detector obtains calibrated intervals, natural near-tie frequency, real GUI proposal quality, multimodal-model benefit, inspection cost, attention-tunneling reduction, token/latency savings, task correctness, input authority, or production readiness. Candidate-count/cost optimization remains #2751's distinct scope.
