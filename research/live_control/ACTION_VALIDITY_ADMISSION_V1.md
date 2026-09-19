# Fresh action-validity admission v1

The retained v31 run makes the next timing problem concrete. The median model
image is about 6.995 seconds old when a plan reaches Executor acceptance, while
a local observation only 123.288 ms old already exists. The current runtime can
invalidate the cover on typed health evidence, but the returned immediate action
does not carry its own observable validity contract.

`action_validity_admission_v1.py` adds a model-free boundary for that missing
step. A contract binds the exact action payload, source observation, focus,
surface, geometry, maximum current-snapshot age and a nonempty conjunction of
typed observable predicates. Immediately before final Executor admission, the
runtime checks a newer snapshot. Action, state binding, sequence, age, unknown
signal and predicate failures remain distinct typed outcomes.

`VALID_CURRENT` means only that the authored observable predicates still hold.
It permits the action to proceed to the existing Executor admission boundary;
it does not issue input or grant authority. Empty contracts and missing required
signals fail closed. `action_validity` must remain separate from
`next_cover_validity`: the former checks whether the newly returned immediate
action is still applicable, while the latter controls already admitted local
behavior during the next planner wait.

## Retained-trace construction replay

The model-free replay projects the latest exact health at each of the five v31
historical plan acceptances. Four changed while the model was running:

| iteration | source health | current health | strict unchanged | fixed bounded-health candidate |
| ---: | ---: | ---: | --- | --- |
| 1 | 91 | 91 | pass | `VALID_CURRENT` |
| 2 | 91 | 85 | reject | `VALID_CURRENT` |
| 3 | 85 | 79 | reject | `VALID_CURRENT` |
| 4 | 79 | 75 | reject | `VALID_CURRENT` |
| 5 | 75 | 71 | reject | `VALID_CURRENT` |

The first construction used a 250 ms current-snapshot limit and failed retained
iteration 2, whose freshest observation was 333.611475 ms old at historical
acceptance. The replay preserves that failed candidate, then evaluates a 500 ms
candidate with the same health predicates. It requires health at least 45 and
at most eight points below its source. The 500 ms candidate passes all five
historical rows; an injected nine-point decrease rejects. The threshold covers
this small trace and is not calibrated as optimal or human-speed. A separate
control makes `enemy_visible == true` required but supplies it as unknown, which
also rejects. This exposes the important limit: health can prevent one class of
stale action, but cannot establish that firing or strafing is currently useful.
A future live schema must have the planner author action-specific predicates,
and the runtime needs extractors for every required predicate it agrees to
evaluate.

The first action-specific extension now supplies exact screen-derived ammo for
fire-bearing MAP01 commands. See
[`MAP01_ACTION_VALIDITY_SIGNALS_V1.md`](../doom/MAP01_ACTION_VALIDITY_SIGNALS_V1.md).

The contract values are synthetic construction inputs. They were not authored
in the retained v31 run and the replay performs no model call or input. It proves
state-machine discrimination only, with no speed, safety, gameplay or task-
completion claim.

The architecture follows the narrower execution-monitoring idea that conditions
can be attached to particular operators and checked incrementally from only the
required state streams. It also retains a large action space by intervening on
specific invalid state-action pairs rather than treating every state change as
a failure. These sources motivate the separation; they do not validate this
implementation:

- Kvarnstrom, Heintz and Doherty, [*A Temporal Logic-Based Planning and
  Execution Monitoring System*](https://cdn.aaai.org/ICAPS/2008/ICAPS08-025.pdf),
  ICAPS 2008.
- Wagener et al., [*Safe Reinforcement Learning Using Advantage-Based
  Intervention*](https://proceedings.mlr.press/v139/wagener21a.html), ICML 2021.

## Reproduce

```powershell
python research/live_control/replay_action_validity_v31_v1.py --out research/live_control/results/retained-v31-action-validity-replay-v1
python -m unittest research.live_control.test_action_validity_admission_v1
```
