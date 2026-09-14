# Mindustry anchor-first Conveyor selection v2

## Question

Does the verified anchor-first semantic evidence path transfer from OpenTTD's
top toolbar to Mindustry's dense lower-right build palette without adding another
agent or granting click authority from icon appearance alone?

The fixed task is to select Conveyor in the visible paused Mindustry build palette
without placing a block. This is a selection task, not the earlier eight-conveyor
construction benchmark.

## Development finding and retained v1 failure

A model-free development probe showed that pointer movement to the Conveyor cell,
followed by bounded pixel settling, produces a persistent panel containing the
Conveyor name, key binding and copper cost. Four later observations reused the
same pixels without a click.

The first preregistered allocation then failed after producing one verified hover
receipt. The OpenTTD compact builder assumed a fixed 62-pixel row, but the
Mindustry evidence crop was 314x100 pixels. It raised
`displayed tooltip exceeds compact row` before the second model call or target
click. Its 20 runtime events, one completed released hover, one 9,300-input-token
candidate call, zero button-down admissions and cleanup are retained.

## Presentation correction

`compact_hover_sheet_v2.py` derives display scale and row height from verified
evidence dimensions under fixed width and height limits. It preserves the exact
640x86 RGB output of the prior OpenTTD one-receipt sheet. For Mindustry it uses
scale 1 and row height 104, producing a 640x128 sheet. The runtime crop digest
still has to match the receipt before presentation.

This changes evidence layout only. It does not change model instructions,
receipt authority, input admission or the task oracle.

## Preregistered v2 result

- app: Mindustry v160.2 on private Linux/Xvfb;
- task: select Conveyor without placing a block;
- model: requested `gpt-5.6-luna`, low reasoning;
- subagents: zero;
- source-derived palette boundary: left 965, top 545;
- detected palette: 4x4 cells;
- model coarse point: `[1004,578]`;
- normalized screen-derived cell: `[1007,577]`;
- verified click-free receipts: one;
- evidence decision: `EVIDENCE_BOUND`;
- button-down admissions in the whole run: one, belonging to the final
  `select-conveyor` operation;
- exact frames: 15;
- socket exchanges including setup and finish: six.

The hover-only frame fails the independent selection oracle. After the admitted
click and movement back to `[640,400]`, both the fixed-fixture Conveyor title crop
and selected-cell border crop match the independently retained successful frame.
The existing engine evaluator also records no collateral target-region tile,
resource or delivery-layout mutation. Event history shows no world-coordinate
button press.

## Timing and input

| Measure | Result |
| --- | ---: |
| Fresh palette detection | 92.467 ms |
| Hover acceptance to first useful image ready | 466.619 ms |
| Hover submission to terminal reply | 909.187 ms |
| Decision start to verified receipt ready | 13,634.470 ms |
| Decision start to semantic selection | 20,770.975 ms |
| Decision start to independent selection oracle | 23,537.664 ms |
| Candidate-call input | 9,300 tokens |
| Receipt-decision input | 8,115 tokens |
| Total measured input | 17,415 tokens |

The 466.619ms value is a runtime `image_ready_ns` boundary. The model-facing
caller receives the completed hover exchange after 909.187ms. The larger
decision times include sequential model calls. No human comparison or causal
speedup is inferred.

## Independent audit

Windows and WSL audits reconstruct all 15 AIT frames, verify preregistered source
hashes and the retained v1 failure, replay palette detection and point
normalization, rebuild the evidence sheet, check both raw Luna outputs against
their schemas and receipts, evaluate pre-click and post-click crops, inspect the
single button admission, verify every terminal release and confirm runtime
cleanup.

Decision: `RETAIN_MINDUSTRY_ANCHOR_TRANSFER`.

## Limits and next step

This is one fixed-layout, paused palette selection. It proves a scoped
cross-domain transfer of active semantic evidence and exposes/removes one
OpenTTD-specific presentation bound. It does not prove Mindustry placement,
wrong-anchor expansion in this domain, window translation, broad GUI reliability,
causal speedup or human-tempo control.

The next Mindustry step should bind the selected control to one independently
scored placement on changed geometry, while keeping palette selection evidence
and world-target evidence separate. The selection-only run should not be repeated
without a changed layout, target or hypothesis.
