# Persistent visual-effect receipt v1

## Question

The changed-geometry OpenTTD run completed its first road segment on turn5 but
spent five inspection-only model turns before accepting the effect. This study
asks whether a small local receipt derived only from the presented pixels can
make the persistent change easier to recognize. It does not read the OpenTTD
observer, task score, map tiles or save.

## Archived calibration

`persistent_effect_receipt_v1.py` compares an action crop before the drag, just
after the drag and at a later inspection. With an RGB difference threshold of20,
it reports pixels that differ from the original in both post-action frames. The
receipt explicitly has no semantic authority and does not itself permit another
mutation.

Threshold1000 separates the selected retained examples:

- nine first-time road effects from v6 and v8--v11 are substantial9/9;
- the selected effects retain1,676--2,190 changed pixels in the relevant
  first-segment cases;
- two v6 drags over an already completed segment are limited2/2, retaining only
  116 and13 changed pixels;
- an exact no-change control has zero persistent pixels;
- five malformed input controls refuse.

This calibration is posthoc. The positive/limited labels were selected using
independent observer history, so the separation is not held-out evidence or a
general effect detector.

## Preregistered model comparison

One frozen v11 turn7 image and prompt are used in A/B/B/A order. Baseline is the
exact original prompt. The receipt condition adds only the compact local receipt.
All four calls use fresh Astra-medium samples; there is no GUI action or retry.

| Endpoint | Baseline | Receipt |
| --- | ---: | ---: |
| checkpoint `observed` | 2/2 | 0/2 |
| checkpoint `uncertain` | 0/2 | 2/2 |
| progress drag proposed | 2/2 | 0/2 |
| inspection proposed | 0/2 | 2/2 |
| input tokens | 34,360 | 34,672 |

The receipt adds312 input tokens, or156 per call. Both receipt samples cite
remaining label occlusion and refuse progression. Both fresh baselines find the
road visually sufficient and propose the same B-to-C route within a one-pixel
offset. The original archived v11 turn7 baseline was `uncertain`, demonstrating
sampling variation even with the frozen context.

## Decision

Reject the v1 prompt form and do not run it live. The explicit
`permits_new_mutation:false` field appears to suppress independent visual
progression along with receipt-only authority. The pixel measurement may still
be useful as a local barrier, but evidence description and action admission must
be separate contracts. A next candidate should let the planner author a bounded
visual postcondition before execution and use it locally between already-planned
steps, rather than asking another model call to reinterpret an advisory receipt.

No correctness, speed, population, causal, token-saving or general visual-effect
claim follows.

Primary evidence:

- `results/persistent-effect-receipt-v1-probe.json`
- `results/persistent-effect-decisions-01/preregistration.json`
- `results/persistent-effect-decisions-01/audit.json`
