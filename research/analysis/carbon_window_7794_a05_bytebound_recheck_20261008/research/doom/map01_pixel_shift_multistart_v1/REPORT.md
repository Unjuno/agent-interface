# MAP01 pixel-registration multi-heading transfer — retained result

Issue #747. Two allocations are retained separately.

## A1 — supervision failure

`MAP01-PIXEL-SHIFT-MULTISTART-20260917-003` froze the exact #719 metric and a 16-case multi-heading matrix. Its sole monolithic formal invocation was terminated by outer container supervision after 5 complete cases and during the sixth. No A1 case ID was rerun. `A1_STOP.json` records `INCOMPLETE_SUPERVISION_TIMEOUT`; the frozen audit fails only because 11 planned result files are absent. A1 contributes no scientific PASS/FAIL denominator.

The five complete A1 rows were all within the independent ±6° yaw gate, but they are retained only as incomplete-allocation evidence.

## A2 — supervision-only repair

A2 (`MAP01-PIXEL-SHIFT-MULTISTART-20260917-004`) changed only allocation/case identity and outer supervision: one fresh case per outer invocation, consume-before-run ledger. Exact metric bytes, runtime dependencies, IWAD, seeds, setup headings `{0,12,24}`, displacement cases `{3,6}`, 34 px gate, 90 ms pulse / 100 ms settle, six-correction budget, and independent ±6° evaluator rule were unchanged. `run_case.py` differs from A1 only in the task identity literal.

All 16 A2 first outcomes completed exactly once; same-ID reruns = 0. Frozen audit passes, verifier passes, and frozen source rehash is exact.

### Raw result

- Main cases within ±6°: **11/12**.
- False `MATCHED` outside ±6°: **0/12**.
- Nonzero-reference-heading main cases correct: **7/8**.
- Material heading diversity was achieved: reference-yaw spans were **135.35°**, **135.35°**, and **131.84°** for the two main seed blocks and aligned-control block.
- Aligned controls: **3/3 `MATCHED` with zero correction input**.
- Missing-reference control: **`UNKNOWN_MISSING_REFERENCE` with zero correction input**.
- Release/keymap/owned-key checks pass; deaths = 0.

The one nonpassing main case was seed 996302, setup12, displacement6. It started at yaw error -33.398° with estimated shift -158 (`CONTINUE`), then after one correction returned shift +160 at the search boundary and therefore **`UNKNOWN_BOUNDARY`**. Independent yaw was still **-28.125°**. This is fail-closed rather than a false success, but it falsifies full multi-heading transfer under the frozen gate.

## Frozen scorer mismatch retained

The frozen A2 aggregator emitted `HOLD_REFERENCE_DIVERSITY_NOT_REALIZED`. That automated label is retained unchanged, but its implementation accidentally added an unpreregistered requirement that repeated reference captures at the same setup heading differ by no more than 0.25°. Issue #747 preregistered only a >=90° span across setup0/12/24. The actual spans exceed 90° in every block.

`POSTFORMAL_RECONCILIATION.json` applies only the preregistered Issue #747 decision rule to the immutable A2 result and yields:

**`HOLD_CROSS_SCENE_TRANSFER`**.

No formal case, source, threshold, heading, or result was rerun or changed to obtain that reconciliation.

## Interpretation

The exact #719 horizontal-registration stopping rule transfers across substantially different MAP01 reference headings in 11/12 frozen cases and never produces a false `MATCHED` in this block. It is not fully robust: one setup12/displacement6 case becomes ambiguous at the ±160 px search boundary while still 28.125° from reference.

This supports retaining the estimator as a useful local relation, but **does not justify cross-scene reliability or runtime promotion**. The next discriminating mechanism should explain the boundary ambiguity (e.g. whether it is merely bounded search-range exhaustion or a deeper perspective/correspondence failure) without tuning the existing 34 px stop gate on this result.

## Retention boundary

GitHub publication retains readable report/summary/reconciliation, A1 stop/completed-row evidence, the exact frozen A2 source files and source hashes, A2 freeze/audit/ledger/verifier receipts, and per-case result SHA-256 identities. Full per-case result JSON/PNG bytes and the deterministic compact evidence archive remain experiment-container/conversation-side; their digests are retained, but their bytes are **not** claimed GitHub-retained.
