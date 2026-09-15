# Action-grounded memory ablation live v1

## Frozen question

On the same current Chromium state and exact task, does an action-grounded target
crop preserve target-selection correctness with less actual model input than a
prior full frame, and does it avoid harming decisions when the old appearance is
duplicated or misleading?

## Conditions

The model, effort, task prompt, output schema and independent server-side scorer
are fixed. Each arm starts a fresh browser/runtime session. Within a scenario the
page URL and current screenshot must be byte-identical across all three arms.

| Arm | Model-visible images |
|---|---|
| no prior visual memory | exact current frame |
| prior full frame | exact current frame + frozen prior 1280x800 frame |
| action-grounded crop | exact current frame + frozen 42x18 target crop |

All arms receive the same short provenance facts in text. Only the presence and
form of Image 2 changes. A flat endpoint schema is checked by one no-GUI/no-input
preflight before the comparison.

The three held-out pages are:

1. `shifted`: real and preview forms are separated; the preview label differs.
2. `duplicate`: both buttons say Save and the real form moves to the other card.
3. `restyled_trap`: the real Save is restyled while the preview retains the old
   button appearance, so blind crop matching points toward the decoy.

The Latin schedule contains nine Luna-low calls, plus one schema preflight, with
zero retry. A model point is acted through Executor v13 after a fresh coherent
post-model observation. The private HTTP fixture independently records correct
Submit, decoy Submit or no effect. Every admitted program must end with empty
verified input release.

## Frozen decisions

The allocation is mechanically valid only if the preflight and all nine arms
complete, each scenario has one byte-identical current screenshot across arms,
and all input releases verify. The crop is eligible for a different-domain
transfer only if it is3/3 correct, causes zero wrong-target actions, is no less
correct than both controls, and uses fewer actual input tokens than full-frame
memory. If no-memory is already perfect, this study does not establish a benefit
over omitting history.

The first outcome is retained without retry. This finite block cannot establish
general memory utility, token savings, latency improvement or human-tempo control.
The source and schedule are hash-frozen in
`action_grounded_memory_ablation_live_v1_prereg.json`; formal output is absent.
