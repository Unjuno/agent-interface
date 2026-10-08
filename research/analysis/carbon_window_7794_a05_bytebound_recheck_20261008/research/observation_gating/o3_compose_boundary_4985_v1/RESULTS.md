# Results — #4985 composition boundary

## Outcome

`PASS_COMPOSITION_BOUNDARY_SCOPED`; interpretation remains `HOLD_CALLER_TYPE_CONTRACT`.

- 8/8 frozen cases reconciled by the independent auditor; `errors=[]`.
- Auditor mutation controls: 5/5 rejected.
- Same-type int/int and str/str positive controls: all three paths admit (2/2).
- Decimal-equivalent int/string pairs: the direct evaluator and standalone verifier admit both (2/2); composed `evaluate_delivery` refuses both with `source_window_mismatch` (0/2 adapter admissions).
- Unequal int/int and str/str controls are refused by all paths.
- bool/int and float/int equality edge controls are refused by the standalone verifier and evaluator. Python equality at the adapter's initial XID check treats these pairs as equal, but the downstream gate's `str()` comparison refuses; composed adapter remains fail-closed.
- Total action emissions 0; GUI calls 0; model calls 0; authority grants 0. Rejected adapter cases are marked model-escalation-eligible; no model was called.

## Interpretation and limits

This confirms an observable difference between two pure primitives and their composed adapter on the frozen main source. The adapter blocks the mixed-type pairs earlier with strict, cross-type Python inequality. The bool/int and float/int cases show that this equality check does not itself enforce exact Python types, although the following string-comparing gate refuses those particular values.

Repository code also shows the capture transport creates receipt XIDs via `int(trusted_window["xid"])`. The experiment did not execute or establish every trusted-window caller, parser, or external serialization contract. Therefore this is not a live bypass, regression, exploitability, or product/security claim. The API's normative XID type remains unresolved; no runtime modification is proposed.

## Provenance

The sole formal run was one local Docker invocation on the pinned linux/amd64 image, exit 0, wall time 1.901 s. Runner and separate independent auditor exit codes were both 0. No retry. See [formal/RUN.json](formal/RUN.json) and the complete row-level [formal/raw.json](formal/raw.json); stdout/stderr and exit receipts are retained alongside.
