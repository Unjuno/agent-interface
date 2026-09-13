# OpenTTD changed-initial-UI probe

Status: one preregistered changed-initial-state episode passed; no route or
speed promotion.

## Question

The first three fixed-Astra successes all began from the same canonical save
with the road-construction toolbar closed. The next allocation retained the
same task, save, prompt policy, model route and independent engine score, but
opened the road toolbar with one recorded setup click before the timed initial
observation. The setup click is excluded from task actions.

The study was preregistered before execution. Static inspection then found four
wrong dictionary-key names in the initial-score assertions. No GUI episode or
model call had begun. The original preregistration remains unchanged and a
separate pre-execution amendment records only that implementation correction.

## Initial-state gate

The runtime sampled the engine after the setup click and before exposing the
first task observation:

| Check | Initial value |
| --- | ---: |
| Target has owned road | false |
| Target is bidirectionally connected | false |
| Forbidden row is clear | true |
| Surrounding road and ownership are unchanged | true |

The initial task score was false and no surrounding tile changed. The initial
screenshot visibly contains the Road Construction toolbar. Its declared
310x50 comparison crop differs from the prior closed-toolbar frame at 11,696
pixels. The canonical save SHA remains
`7836587d28056c534dd3ce2968fc89d3e9b47e28400afc90234954a470f8e97c`.

## Result

Fixed Astra-medium requested independent verification on turn 6. The engine
confirmed target ownership, bidirectional connectivity, a clear forbidden row
and unchanged surroundings.

| Metric | Pre-opened toolbar |
| --- | ---: |
| Hard task success | 1/1 |
| Initial observation to semantic completion | 89.272s +/- 50ms |
| Wrapper-observed model wait | 77.012s |
| Proposal to useful feedback, five acts | 10.363s |
| Model calls | 6 |
| Input / output / reasoning tokens | 97,696 / 1,173 / 698 |
| Exact frames / contact sheets | 24 / 4 |
| Durable calls / append records | 20 / 41 |

Provider receipt, provider first-token, runtime receipt and OS-injection
endpoints remain explicitly recorded as unavailable rather than estimated.

## What changed in the model route

In the prior closed-toolbar episode, the first two turns inspected the main
toolbar and opened Road Construction. With the toolbar already open, the new
first turn immediately inspected its two straight-road tools. The model then
used two turns to select the tool and correct its intended starting point
before dragging. Both conditions therefore used five action turns plus one
verification turn.

The prior closed-toolbar episode took 92.377s, including 79.681s model wait and
10.605s proposal-to-feedback time, with 97,729 input tokens, 28 frames and 20
durable calls. The new episode is descriptively 3.105s shorter, has 2.670s less
model wait, 0.242s less proposal-to-feedback time, 33 fewer input tokens and
four fewer frames. These are unpaired generated episodes with different
initial pixels, model sampling and cache behavior. They do not establish a
causal speedup.

## Decision

Changing the visible affordance was handled correctly, so fixed Astra is now
4/4 across this task family: three closed-toolbar episodes and one pre-opened
toolbar episode. This is the first changed initial UI state, but the same save,
geometry and road objective remain.

Do not promote pre-opening the toolbar as an interface optimization. It removed
toolbar discovery but did not reduce model turns or durable calls; semantic
work shifted to tile targeting. The next OpenTTD allocation should change task
geometry or objective structure and keep the same independent completion gate.
A human control remains required before any human-tempo claim.

Windows and WSL audits pass. Primary artifacts are under
`results/timing-envelope-openttd-matched-04/`.

