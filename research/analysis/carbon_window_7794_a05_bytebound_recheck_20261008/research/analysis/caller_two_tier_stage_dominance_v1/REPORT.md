# #1916 adaptive caller two-tier stage dominance

Decision: **PASS_CALLER_TWO_TIER_STAGE_DOMINANCE_SCOPED**.

## Exact source
The analysis is bound to `research/live_control/adaptive_acquisition_caller_v3.py` Git blob
`7faf042304728ce91a3e4f89d465b251ea0bf70d`.

Exact-source audit finds one call site each:
- `reuse_revalidate`: line 371;
- `final_revalidate`: line 392;
- `execute`: line 399.

Line 393 immediately returns `stop(revalidation)` whenever the final result is not `revalidated`.

## Proof by reuse-route cases
After a reuse route loads the cached target, it must enter `reuse_revalidate`.

1. **reuse succeeds** — sets `repair_path="none"`, leaves the reuse branch, and joins the common `final_revalidate`.
2. **local repair succeeds** — sets `repair_path="local"`, leaves the reuse branch, and joins the same common `final_revalidate`.
3. **model repair succeeds** — `model_repair` can return `None` only after target reference acquisition plus post-model current-patch validation. Control then leaves the reuse branch and joins the same `final_revalidate`.
4. **reuse failure not authorized for repair** — returns `stop` inside the reuse branch, before final revalidation.
5. **model repair failure** — `model_repair` returns a stop result; the caller returns it before reaching final revalidation.

At the common final gate, every non-`revalidated` result returns before the sole `execute` call site. Therefore every reuse-route path that reaches `execute` has passed both the reuse-layer decision topology and the common final gate.

## Consequence
The unchanged caller topology is structurally compatible with the #1835/#1848 split:
- reusable/versioned evidence can naturally belong to `reuse_revalidate`;
- fresh commit-bound evidence can naturally belong to `final_revalidate`;
- `execute` is dominated by the final gate.

This does **not** prove that the #1900 bridge supplies the correct receipts. #1900 remains a retained `HOLD_SOURCE_TRANSPORT` with scientific formal invocation 0.

## Limits
This is source-bound control-flow analysis, not executable bridge evidence, GUI/input evidence, latency measurement, or a claim about future caller revisions. Any caller source change requires re-audit.
