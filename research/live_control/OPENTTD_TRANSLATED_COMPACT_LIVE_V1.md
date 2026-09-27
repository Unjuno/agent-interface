# Translated OpenTTD compact active evidence v1

## Result

One preregistered fresh OpenTTD allocation moved the live X11 surface before any
model decision, derived the toolbar from the changed screen, and used compact
persistent-hover receipts for the actual target click. The same Luna-low model
made both semantic decisions. No subagent participated in perception, judgment,
operation or token accounting.

The requested test move produced an observed surface delta of `[21,28]` and
changed the application geometry from `[129,40,1024,720]` to
`[150,68,1024,720]`. The previous toolbar row assumption was 40. The new
position-independent detector found the unique 30-slot row at y=68 in 154.287ms.

From the moved full screen, the model proposed `[506,79]` as its direct coarse
point. The detector expanded around the corresponding slot to:

```text
[456,79] [479,79] [506,79] [529,79] [552,79]
```

Five 800ms persistent hovers ran in bounded 3+2 batches. The compact sheet
contained only verified tooltip pixels and receipt/point bindings. Luna selected
receipt 3 at `[506,79]`, whose tooltip identifies company finances. Exact
rehover matched the original receipt, the ordinary click released, and the
independent title oracle passed at the title box shifted only by the observed
surface delta.

| Measurement | Observed value |
|---|---:|
| Dynamic toolbar detection | 154.287ms |
| Five hover batches | 6,198.997ms |
| Candidate-model input | 9,294 tokens |
| Compact-evidence input | 8,277 tokens |
| Decision start to independent evaluation | 29,638.731ms |
| Exact retained frames | 50 |

The task-specific finance oracle is true. The harness also emits its original
road-construction score, which is false because this allocation deliberately
does not build roads; it is unrelated to the finance-window task and is retained
explicitly rather than counted as success.

## What changed

The earlier detector read a fixed y=40 row. `openttd_toolbar_slots_v2.py`
converts the image once and scans all rows for 20–24px edge-color runs. It accepts
only a unique row with the maximum repeated slot count. Three archived synthetic
translations recover all 30 points exactly; a missing-toolbar image is refused.
The first correct version repeatedly converted the image and took about four
seconds. It was replaced before formal allocation by the single-scan version,
which takes roughly 124–160ms in the cross-OS probes.

`openttd_finance_oracle_v2.py` translates the frozen RGB title box using only the
observed whole-surface delta. Its probes accept the correct translation, score a
stale or one-pixel-wrong delta false, and refuse out-of-bounds regions.

## Audit and limits

The Windows and WSL audit reconstructs all 50 AIT frames, model events, reported
usage, dynamic slots, 3+2 receipt batches, compact pixels, strict binding,
rehover, release and independent oracle. All preregistered implementation and
task-source hashes match. The first audit attempt used the wrong decoder stream
name and stopped at frame 1; correcting it to the runtime's unchanged
`live-control` stream makes both audits pass. The runtime did not change stream
identity at the surface move.

This is one fixed-seed application translation. It proves neither resize/reflow,
unknown-app or cross-toolkit transfer nor a matched speed/token improvement.
29.639s is still far from ordinary human tempo. The 6.199s five-hover stage is
the largest deterministic delay. The next candidate should probe the model's
anchor first, allow the same model to accept its verified tooltip or request a
bounded neighbour expansion, and retain the earlier confidently wrong anchor as
the required recovery case.

Artifacts are in `results/openttd-translated-compact-live-01/`.
