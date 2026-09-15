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

## First outcome

The schema preflight and all nine arms completed on the first allocation. Each
scenario's three current PNGs are byte-identical. Every model target was executed
through the fresh observation and Executor boundary; all nine server records are
exact real submissions, with zero decoy/no-effect result and empty verified
release for every program.

| Arm | Correct | Wrong target | Input tokens | Images |
|---|---:|---:|---:|---:|
| no prior visual memory | 3/3 | 0 | 28,035 | 3 |
| prior full frame | 3/3 | 0 | 31,791 | 6 |
| action-grounded crop | 3/3 | 0 | 28,188 | 6 |

Against full-frame history, crop retained correctness and used3,603 fewer input
tokens (11.33%). Against no visual memory, it added153 tokens (0.55%) and did not
improve correctness. In the deliberately misleading condition, the crop arm
explicitly returned `rejected_as_stale_or_misleading` and selected the current
real target. Under the frozen rule, crop is eligible for a different-domain
transfer as a replacement for full-frame history; no-memory remains the simpler
default on this fixture.

The original audit stopped with `KeyError: requested_model`: the machine prereg
omitted that redundant display field. This is retained. The hash-frozen runner
hard-coded Luna-low before allocation, and all ten raw call plans independently
record Luna-low. A separately versioned retained audit verifies raw prompts,
images, usage, call IDs, current-frame identity, model points, Executor programs,
server records and releases on Windows/WSL without rewriting or rerunning output.
The retained receipt covers303 files / 5,497,337 bytes, including the original
audit traceback, diagnosis, raw CLI events, exact screenshots, Executor events,
HTTP oracle records and both successful audits.

This finite three-task-per-arm block does not establish general memory utility,
latency improvement or human-tempo control. Model-wait totals varied in an
uncontrolled service order and are descriptive only. The next step is transfer
to an OpenTTD or Mindustry transition where prior visual evidence is actually
needed; retaining a crop should remain conditional rather than become default.
