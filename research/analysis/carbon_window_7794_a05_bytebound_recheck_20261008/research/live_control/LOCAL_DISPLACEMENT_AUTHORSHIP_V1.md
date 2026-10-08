# Model-authored local displacement postcondition v1

## Question

The scripted local displacement condition distinguishes a24px target from a20px
partial move. This fixed-context study asks whether a model can select a valid
source patch from the presented screenshot. It does not execute GUI input.

## Preregistered design

One retained exact1280x800 initial Inkscape frame and one fixed prompt are used
in Luna/Astra/Astra/Luna order. Luna uses low effort and Astra medium. Each route
gets two first outputs with no retry or replacement. The prompt fixes the task,
24px delta, tolerance, sample count, interval, timeout and failure behavior. The
model authors the target patch and identifier.

The primary endpoint requires strict JSON that constructs the local condition,
returns `met` on the retained exact24px pair and returns a non-met outcome on the
retained exact20px pair.

## Result

| Endpoint | Luna-low | Astra-medium |
| --- | ---: | ---: |
| strict primary pass | 2/2 | 2/2 |
| full red-bbox coverage | 2/2 | 2/2 |
| input tokens | 25,480 | 30,812 |
| cached input tokens | 9,728 | 13,056 |
| output tokens | 292 | 197 |
| runner wall samples | 8.493s,6.442s | 11.483s,10.066s |

Both Luna samples and one Astra sample choose
`[590,367,60,48]`; the other Astra sample chooses
`[588,365,64,52]`. All four immutable anchors locate24px in both target samples
and20px in both partial samples. No call adds prose, fields or action authority.

## Decision

Advance the authorship signal to one fresh live transfer while retaining the
same narrow moved-object task. Do not promote the operation. The prompt fixes
most contract fields, the evaluation reuses one source image and two retained
effect pairs, and there is no model-controlled pointer path. The wall and token
samples are descriptive and do not establish a Luna/Astra comparison.

Road placement remains outside this result because it needs target-and-guard
visual structure rather than displacement.

Primary evidence:

- `results/local-displacement-authorship-01/preregistration.json`
- `results/local-displacement-authorship-01/execution.json`
- `results/local-displacement-authorship-01/audit.json`

Follow-up: the unchanged first Luna condition now passes one separately
preregistered fresh target/partial transfer after two retained integration
failures. See `LOCAL_DISPLACEMENT_TRANSFER_V1.md`.
