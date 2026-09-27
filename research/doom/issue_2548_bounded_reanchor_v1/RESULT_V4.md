# Formal result: Issue #2548, allocation v4

Disposition: `PASS_BOUNDED_REANCHOR_PRESERVES_SAFETY_SCOPED`.

| Case | Guard only | Receipt gate | MAE / reason |
|---|---|---|---|
| coast, no reanchor | ADMIT | no fresh receipt | MAE 0.0143877 |
| drift, no reanchor | REJECT_CONTEXT_CHANGED | no fresh receipt | MAE 0.0441826 |
| drift, same-session fresh | REJECT_CONTEXT_CHANGED | ADMIT | fresh MAE 0.0036223 |
| coast, same-session fresh | ADMIT | ADMIT | fresh MAE 0.0000991 |
| stale receipt reuse | REJECT_CONTEXT_CHANGED | REJECT_PROVENANCE | stale/duplicate sequence |
| foreign-session receipt | REJECT_CONTEXT_CHANGED | REJECT_PROVENANCE | session identity mismatch |
| incomplete receipt | REJECT_CONTEXT_CHANGED | REJECT_PROVENANCE | missing frame hash |

All seven live sessions completed. Every terminal release was verified with empty keys and buttons. Every independent score reported zero kills, zero deaths, no map exit, and no dead player. The independently invoked Docker audit recomputed the exact seven-case matrix, receipt/session/sequence bindings, RGB frame hashes and guard/reanchor MAE values: `PASS`, zero errors. Its separate mutation check rejected empty and truncated result sets, failed terminal, unverified release, nonzero death, and a foreign-session mutation.

The v4 source freeze is `FREEZE_v4.json`; formal raw event streams, frames, runtime evidence and results are under `formal_v4/`. Run configuration used local Docker, `--network none`, read-only source mount, two CPUs, 4 GiB memory and 128 PIDs. No workflow executed these sessions.

This is limited to receipt provenance and visual-pair admission in the fixed ViZDoom fixture. It does not prove semantic correctness of a newly planned action, general task recovery, or production safety. Formal v3's execution is retained but its PASS qualification was withdrawn after review; see `REVIEW_RESPONSE.md`.

## Routing and action-authority limit

Issue #2548 remains closed as `not_planned`. Its 2026-09-22 routing update prefers #615/#629: reuse the already captured post-recovery observation as no-authority planner context and bind a new planner outcome to that receipt. This experiment measures the historical extra-observation pair gate only. It does not compare the utility or cost of that extra observation against #615's receipt reuse, does not reopen #2548, and does not supersede #615/#629. `ADMIT` denotes visual-pair eligibility only; this runner grants no action authority and dispatches no post-reanchor action.
