# Chromium compiled GUI live-v5 — state-scoped dependency static probe

This probe reads the **existing frozen v5 interface declaration** from `run_compiled_gui_interface_live_v5.py`. It does not rerun or alter the consumed live allocation.

The v5 interface declares four predicates:

- `field_pixels_changed`
- `field_target_present`
- `submit_target_present`
- `submission_pixels_changed`

The method states are `empty -> filled -> submitted` with actions `enter_token` then `submit_form`.

Using the same derivation rule as `COMPILED_GUI_INTEGRATION_PROBE.md` (state branch conditions + possible action symbol identity/dependencies + incoming expected-effect predicates):

| state | current interface-wide predicate count | derived required set |
|---|---:|---|
| empty | 4 | `field_pixels_changed`, `field_target_present` (2) |
| filled | 4 | `field_pixels_changed`, `submit_target_present` (2) |
| submitted | 4 | `submission_pixels_changed` (1) |

Finite enumeration of all four boolean predicate values gives 16 observations/state, 48 total. For every observation:

- branch match vector under the projected state-scoped observation equals the full observation;
- all identity/dependency predicates of a matched target symbol are present;
- all incoming pending-effect predicates are present.

Result: **48/48 structural checks pass**.

For the three-observation positive path, the declared predicate-field budget is 12 with the current interface-wide request versus 5 with the derived state-scoped request: **7 fewer fields (58.3%)**. This is a field-count result only; no token or live acquisition saving is inferred.

The retained live-v5 changed case navigates to `about:blank` after the first action. In state `filled`, `submit_target_present` remains in the derived set, so the known missing-submit safety signal is not removed by this projection. This is a structural observation, not a replay of the consumed allocation.

## Decision

**ADVANCE** one new, separately versioned development/live candidate in which only the observation adapter's requested predicate set is narrowed per state. Preserve the exact v5 method, actions, scorer, admissions, target checks and typed-yield behavior. Do not rerun the v5 allocation ID or infer token savings from this static result.