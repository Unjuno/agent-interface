# MAP01 command-effect receipts

The visual-stagnation experiment showed that a repeated-view label does not say
which command failed. This experiment instead derives a visual receipt for every
semantic motor command. The shared X11 `hold` operation already captures exact
frames while a key is held, so the controller reuses the final existing sample
for each command. It adds no executor step, input hold, or observation request.

The receipt compares the viewport before and after one semantic command at
64x45 grayscale. Normalized mean absolute error at or below 0.015 becomes
`no_visible_effect`; larger change becomes `visible_change`. This is pixel
evidence only. It does not establish collision, position, door state, damage,
or semantic task progress.

An initial collector incorrectly expected exactly one observation per hold.
A 600 ms hold actually emitted seven in-hold samples plus the explicitly added
observation. The run stopped after one model call and is retained. The corrected
controller groups all existing samples by command step and uses the final one.

## Same-seed feasibility

Three ordered 12-decision allocations used Luna low, normal MAP01, skill 1,
seed 990608, and four-turn model sessions. The verbose candidate exposed every
receipt field to the planner. The compact candidate retained complete local
receipts but sent only the action names whose visible effect was below the
threshold.

| Allocation | Exit | Wall s | Model s | Non-model s | Input tokens | Uncached input |
|---|---:|---:|---:|---:|---:|---:|
| baseline | no | 100.951 | 84.437 | 16.514 | 118,109 | 17,117 |
| verbose receipts | no | 125.636 | 108.920 | 16.715 | 123,985 | 48,721 |
| compact receipts | no | 110.181 | 95.400 | 14.781 | 119,105 | 51,393 |

The verbose planner projection contained 6,933 dynamic characters over twelve
turns. Sending only no-effect action names required 29 characters, a 99.582%
reduction for that dynamic field. Actual total input was 0.843% above baseline
for the compact arm. Cache allocation varied sharply, so neither uncached-token
nor model-time changes are attributed causally to the representation from this
ordered sample.

The compact arm exposed three no-effect actions. Luna changed its immediate
next action all three times. All arms remained unfinished with zero deaths and
kills, so this establishes mechanism use, not gameplay improvement.

## Longer matched pair

A second seed, 990609, ran the baseline first and compact receipts second for
40 decisions each.

| Allocation | Exit | Deaths | Kills | Revisits | Wall s | Model s | Input tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | no | 0 | 0 | 8 | 357.215 | 308.012 | 394,194 |
| compact receipts | no | 0 | 0 | 9 | 352.516 | 301.128 | 396,340 |

The compact arm was 1.315% shorter in wall time and used 0.544% more total input
tokens. It had three no-effect exposures and zero immediate repeats of the
listed action. It did not reduce revisits or improve the independent game
score. This single ordered pair does not prove a speed gain.

Across the long pair, command issue to first visual feedback had medians of
45.15 ms for baseline and 47.17 ms for compact receipts. The compact receipt
endpoint median was 390.22 ms. The important remaining delay is downstream:
from a no-effect observation to admission of the next model-authored plan took
8,682.54 ms median in the long compact run. The interface already observes the
effect quickly, while recovery waits for another model round trip.

The next candidate should let the model attach a bounded contingency to a
semantic command, such as stop or execute a different short action when the
visual effect is absent. The local executor can then act near the receipt
endpoint instead of waiting roughly nine seconds. It must record the condition,
branch admission, recovery result, extra input round trips, and any false branch.

Run the repository-backed audit with:

```sh
python research/doom/audit_map01_effect_receipt_v1.py
```

The committed record contains source frames, contact sheets, plan timing events,
model/token reports, environment and independent scorer output, exact controller
sources, and the initial invariant failure. Full streams remain in
`results-local/doom`.
