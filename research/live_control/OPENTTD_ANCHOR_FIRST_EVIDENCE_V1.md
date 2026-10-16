# OpenTTD anchor-first active evidence v1

## Result

The interface can inspect one verified anchor tooltip first, accept it when it
matches the task, and request bounded neighbour expansion when it does not. The
same Luna-low model makes the semantic decision. No model confidence field or
subagent authorizes input.

A fixed Correct/Wrong/Wrong/Correct allocation used two archived receipts:

- correct: the translated finance anchor at `[506,79]`;
- wrong: `[436,51]`, which the earlier model had called
  `visually_unambiguous` even though its tooltip identifies another control.

All four preregistered decisions are correct. The correct receipt returns
`target_reference` twice. The retained wrong receipt returns `expand_search`
twice. Every decision cites receipt1 and its exact point; expansion grants no
target or input authority. Each call reports 8,096 input tokens.

## Fresh live use

One preregistered translated OpenTTD episode then uses the staged policy. The
fresh model proposes `[505,79]`; screen-derived slot geometry normalizes it to
`[506,79]`. Only that slot is hovered initially. The persistent tooltip says
company finances, so Luna returns a receipt-bound target instead of expansion.
Exact rehover still occurs before ordinary click, and the shifted independent
finance-title oracle passes.

| Metric | Prior five-first live | Anchor-first live |
|---|---:|---:|
| Initial hover submit-to-return | 6,198.997ms | 1,283.273ms |
| Durable calls | 16 | 14 |
| Exact frames | 50 | 39 |
| Decision-to-independent-evaluation | 29,638.731ms | 25,963.985ms |

The initial hover stage is 4,915.724ms shorter. This difference is directly tied
to submitting one hover instead of five under the same 800ms persistence rule.
The total path is 3,674.746ms shorter, but the episodes are sequential and model
wait varies, so total time is descriptive rather than a causal speed result.

The fresh path reports 9,288 candidate-model input tokens and 8,098 anchor-
evidence input tokens. The prior path reports 9,294 and 8,277. Prompt/schema and
screen content differ, so this single sequential difference is not promoted as
a token reduction.

Useful timing boundaries are now explicit:

- decision start to verified anchor receipt: 14,197.623ms;
- decision start to semantic selection: 21,090.223ms;
- decision start to independent evaluation: 25,963.985ms.

## Recovery and assurance

`anchor_evidence_contract_v1.py` requires exactly one verified receipt and an
exact point match for both outcomes. `target_reference` remains a reference that
must pass ordinary input admission. `expand_search` is observation-only and
cannot be used as a target.

The live implementation contains the recovery route: after `expand_search`, it
collects the other four radius-two slots in bounded batches, composes all five
receipts, and uses the existing strict selection contract. That branch is not
claimed live-successful yet. The fixed retained wrong receipt proves the model
requests expansion 2/2, but it does not prove fresh expansion execution or final
task recovery.

Windows and WSL audits reconstruct both compact fixed presentations, all four
raw model turns, the 39 live AIT frames, screen-derived slots, receipt pixels,
binding, rehover, releases and independent oracle. Sources and the immutable
five-hover baseline are hash-bound.

## Scope and next step

This supports the anchor-first success branch for one translated OpenTTD task.
It does not establish an order-balanced total-latency gain, live wrong-anchor
recovery, resize/reflow, another application or human-tempo operation. The next
allocation should execute the expansion branch live from a known wrong anchor,
require zero target input before expansion, and independently complete the same
finance task after the full receipt set is available.

Artifacts:

- `results/openttd-anchor-evidence-abba-01/`
- `results/openttd-anchor-first-live-01/`
