# Delayed effect: evidence changes wait versus duplicate input

The previous partial-evidence comparison was confounded because its common
prompt disclosed that Save had already been attempted. This study creates a
state where the screenshot cannot answer that question.

## Actual state preparation

A private Chromium/X11 fixture accepts an ordinary form submission through
`fetch`, waits five seconds, writes the submitted artifact, and returns no page
content. The field remains populated and the page has no navigation/loading or
confirmation indicator. The same pixels are therefore compatible with either
"value entered but not submitted" or "submission completed locally while its
application effect is pending." The controller cannot inspect the server log.

The selected revision sent Return exactly once through the shared input runtime.
The input program completed and released all input. An immediate saved-effect
checkpoint was UNKNOWN because the artifact did not yet exist. After the declared
delay, a new checkpoint was VERIFIED and independent evaluation found exact value
`t000242`. All 10 transported frames reconstruct, 85 runtime events and six
durable calls audit, and the private process/socket closed.

| Interval from input acceptance | Observed time |
| --- | ---: |
| Post-action image ready | 553.444 ms |
| Program terminal | 575.987 ms |
| Explicit UNKNOWN effect | 617.325 ms |
| VERIFIED effect | 5,562.967 ms |

UNKNOWN preceded the delayed commit by 4,862.733 ms. Once the fixture committed,
the next explicit verification completed 82.908 ms later. These are one local
scripted episode's runtime timestamps, not model receipt or a human comparison.

Three development failures are retained. V1 supplied a removed outer caller
option; v2 tried to assign a journal-owned action ID; v3 reused a stale coordinate
after the fixture layout moved and selected the page instead of the field. V4
completed but exposed browser loading state. V5 changed the fixture to `fetch`
and is the selected preparation. V1-v3 produced no committed form artifact.

## Fixed model comparison

Eight predeclared Luna/low calls use the exact same V5 screenshot, common task
prompt and output schema. No proposed action executes.

- A includes strict v3 checkpoint binding, the completed five-step submission
  terminal, prior steps and explicit unknown application effect.
- B includes the same UNKNOWN checkpoint but omits execution, prior steps and
  binding. It represents a caller that has no evidence of prior submission.
- The common rule says a known completed submission inside the delay window must
  wait and check; absence of submission evidence permits one submission. It does
  not state which condition has submitted.

All four A calls choose `wait_and_check`. All four B calls choose the exact
`submit_once` program. No call verifies UNKNOWN. This demonstrates that retained
execution evidence changes the correct next operation in this declared state;
removing it would save tokens by changing semantics, not by lossless compression.

| Condition | Calls | Expected decisions | Input tokens/call | Decision |
| --- | ---: | ---: | ---: | --- |
| A: strict prior execution | 4 | 4 | 9,759 | wait and check |
| B: no prior execution evidence | 4 | 4 | 9,485 | submit once |

The 274-token difference is not a saving available to the strict caller because
the omitted fields are necessary to distinguish a pending effect from a new
action. Four samples per condition on one authored fixture are not a reliability
bound. Runner times and cache counts are archived but do not support latency
claims. The comparison does not cover partial terminals, conflicting visual
evidence, privacy redaction or a real model-driven live wait.

Follow-up: [one fresh live episode](DELAYED_EFFECT_LIVE.md) delivered the strict
UNKNOWN state to the model. It selected wait/check; model computation covered the
remaining application delay, and a single post-model checkpoint verified the
effect with no duplicate input.

Artifacts:

- `results/delayed-effect-01` through `-05`: development and selected preparation
- `results/delayed-effect-decisions-01`: prompts, raw model events and audit
- `audit_delayed_effect_v1.py`: runtime/effect audit
- `audit_delayed_effect_decisions_v1.py`: model decision and token audit
