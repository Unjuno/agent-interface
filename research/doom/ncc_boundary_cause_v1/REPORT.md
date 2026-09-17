# NCC boundary-cause discriminator — retained first outcome

Task `MAP01-NCC-BOUNDARY-CAUSE-20260917-005`, Issue #769.

## Disposition

**`HOLD_NO_RANGE_DISCRIMINATOR`** under the preregistered Issue #769 rule.

The frozen runner itself emitted `HOLD_OR_FAIL_NCC_BOUNDARY_CAUSE`; the read-only reconciliation maps that immutable result to the preregistered HOLD class because the required rigid `UNKNOWN_BOUNDARY` discriminator was not exposed.

## Method

Container-only deterministic 320x140 image fixture. The 34 px stop gate is unchanged. The only estimator parameter changed between arms is horizontal NCC search range:

- `bounded160`: `[-160,+160]`
- `diagnostic240`: `[-240,+240]`

The fixture contains rigid translations, deterministic two-layer parallax, unrelated-image, and low-texture controls.

Construction passed `py_compile` and 7/7 excluded-seed tests. Exact source/cases/ranges/gates were frozen before one formal runner invocation. Formal reruns: 0.

## First outcome

Rigid cases:

- +140 and +158 are identified exactly by both arms.
- +165, +190 and -175 become `UNKNOWN_AMBIGUOUS` under `bounded160`, not `UNKNOWN_BOUNDARY`.
- `diagnostic240` recovers +165, +190 and -175 exactly.

Therefore a finite search range can block recovery of a true rigid displacement, but this authored fixture did **not** reproduce #747's exact boundary-status signature. That prevents the preregistered PASS.

Parallax cases:

- background/world task shifts are +80, -70 and +25 px;
- `diagnostic240` identifies +180, -185 and +170 px respectively, following the deliberately dominant foreground layer rather than the task/background relation.

Thus widening global search range is not a general repair for correspondence-model mismatch.

Controls:

- unrelated images remain `UNKNOWN_AMBIGUOUS`;
- flat images remain `UNKNOWN_FLAT`;
- no control is falsely accepted as aligned.

## Integrity

Formal runner invocation count: 1. Frozen source rehash: 7/7 exact. `verify.py` correctly returns `FAIL_VERIFY decision,gates` because the preregistered PASS gates are not all true. The failed verification is retained; it was not bypassed or rerun after changing source/gates.

## Boundary

This does not explain the exact #747 `UNKNOWN_BOUNDARY` event. It establishes only that (1) rigid beyond-range displacement can be recoverable with a wider search even when the bounded arm fails by ambiguity, and (2) wider global NCC can still be task-wrong under multi-layer motion. Do not widen #747's search range or alter the 34 px stop gate from this result.
