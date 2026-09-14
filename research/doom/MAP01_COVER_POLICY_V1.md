# Model-authored renewable cover policy

Renewal keeps a local program alive while a frontier call is pending, but v18
repeats a controller heuristic. This candidate asks the model to provide a
compact `next_cover` policy together with its current plan. That policy runs
during the following inference interval and can be renewed without another
model call.

The schema permits one to four conservative cover commands. `coast` is used when
no threat is visible. Backward, strafe, fire and retreat-fire are available for
visible danger. Forward, turn and use are excluded because the policy may repeat
from a later, uninspected view. The responder allows fire only when a visible
threat and HUD ammunition support it. Terminal states must return an empty
policy.

Two sequential four-decision Astra-low development runs used normal MAP01,
skill 1 and seed 990612. The initial viewport descriptor difference was below
the no-visible-effect threshold. Both ended alive and deliberately unfinished.

In v19, Astra returned `coast` for clear views. After a door opened and an enemy
with ammunition became visible, it authored short left-strafe, fire and
right-strafe cover. The next iteration executed that exact semantic policy.
Self-use then exposed a compiler defect: adding a one-second coast after every
command exhausted the 16-step cap after 9,640 ms and ended on a hold.

V20 retains v19 and replaces only the compiler. It emits complete policy cycles,
distributes coast time between cycles, ends on coast and totals exactly 10,000 ms
within 16 steps. Unit cases cover coast-only, one-action, two-action and the
observed three-action threat policy. A second live run executed four model-
authored coast policies; two calls required renewal. Its only uncovered model
segments were the 21.512 ms and 20.990 ms release/readmit boundaries.

The corrected same-seed run used 49,360 input tokens versus 48,661 for the prior
renewal-only development probe, a descriptive increase of 699 tokens (1.436%).
The samples are sequential and model outputs differ, so this is not a causal
token-cost estimate. The corrected trajectory did not expose a threat within
four turns, so v19 proves threat-policy handoff while v20 proves the repaired
compiler and live renewal. A new run is required before attributing gameplay
benefit to the corrected threat policy.

The subsequent frozen threat-exposure allocation found another compiler edge:
`coast pulse` expanded to twenty steps and was rejected before cover input. A
conditional schema repair then failed because the response endpoint disallows
`oneOf`. [Cover-policy contract v2](MAP01_COVER_CONTRACT_V2.md) retains both
failures and replaces explicit coast with an empty-array representation whose
entire permitted policy space passes compiler bounds.

Run the audit with:

```sh
python research/doom/audit_map01_cover_policy_v1.py
```
