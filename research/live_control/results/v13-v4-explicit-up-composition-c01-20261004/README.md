# PR #7429 v13 / PR #7449 v4 explicit-up wrapper composition C01

## Question

Can the #7449 `InputTransitionOwnerV4` be wired to the latest #7429 `InputOwnerV13` using the existing constructor injection without adaptation?

## H / T / D / C / U

- **H:** Direct injection is incompatible because v13 inherits v11's typed `input_release_rpc` return while v4's parent transition layer requires an underlying v10 `up` call to return `None`.
- **T:** Pin exact #7429 head `5f3e24d3c177bf32f04c9282750f37b413de816b` and #7449 head `915c46d7f448003d82dd002d6e9fb34141e2712a`. Load the actual v13/v3/v4 source methods. First exercise the exact v13 call wrapper around a mocked None-returning v10 owner call; then pass that return shape through v4 with a fake owner. Xlib imports are stubbed, while display construction and input calls are asserted never to occur.
- **D:** The direct composition is STOP if v13 returns `input_release_rpc` and v4 raises `AssertionError: InputOwner v10 explicit release unexpectedly returned payload` before producing an input-release transition. No exception plus a receipt accepted by v4 would refute H.
- **C:** The candidate demonstrates only API compatibility of these wrappers. It does not show either PR is defective independently, because both have different owner contracts and can be used separately.
- **U:** No owner thread, X server, key state, game, app feedback, recovery or live allocation ran. A future adapter might consume the v11 caller interval while preserving no physical/application claim; that repair is outside C01.

## First outcome and versioning

A01 stopped before importing the v13 candidate because the source snapshot omitted `lease.py`. Its traceback and exit 1 are retained under `PREVIOUS-STOP-A01/`. The dependency was added from the same exact #7429 head for A02; A01 was not rerun or relabeled.

A02 executed once and returned `input_release_rpc` with caller interval `[100,145]` ns. The exact v4 transition wrapper then raised the expected assertion on that dictionary. The probe confirmed no Xlib display or input call. The raw candidate result is `RAW.json`; `audit.py` independently checks the saved decision and source SHA-256 values.

## Scope

This proves that direct dependency injection is not a valid composition of these exact wrapper versions. It does not establish whether a separately designed bridge is correct or whether the per-key server-side receipt from the v12/v4 path should be merged into the v13 cancellation path. No live input or game run occurred.

Reproduce once only as a new construction version, not by rerunning C01-A02. The prior A01 STOP and A02 result are retained as the first outcomes.
