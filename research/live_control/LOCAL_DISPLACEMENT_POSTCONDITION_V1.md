# Local displacement postcondition v1

## Question

The single-ROI change barrier admitted a12px partial effect against a24px
requested move. This candidate asks the agent to declare the target patch and
target displacement before execution, then uses an immutable visual anchor to
check two stable samples inside the already admitted program. It cannot correct
input or grant authority.

## Retained-frame gate

The fixed contract bounds the source sequence, patch to4--96px per dimension,
target delta to +/-32px, tolerance to0--3px, samples to2--3 and timeout to3s.
Binding changes, lost or ambiguous patches, wrong displacement and timeout stop
with `needs_decision`.

The earlier12px partial frame pair stops because the patch is lost under the
retained decoration state. Two independently saved patch-servo cohort03 cases,
at original and shifted source positions, both retain24px displacement for two
frames and pass. Eight malformed contracts and a binding-change control stop.
This is retained evidence and inherits the known template decoration limit.

## Fresh X11 pair

The first allocation is retained as HOLD. Its assumed input-to-screen mapping is
wrong: dense input48px moves the object44px, not24px, and input24px moves it20px.
Both conditions safely stop, with no later Save.

The second allocation fixes only the measured pointer paths and inserts the
existing bounded pixel-settle operation after Escape. It uses fresh Inkscape
sessions in target/partial order:

| Endpoint | Target | Partial |
| --- | ---: | ---: |
| pointer path delta | 28px | 24px |
| independently reconstructed visual delta | 24px | 20px |
| two anchor samples | 24px, 24px | 20px, 20px |
| postcondition | met | target_not_reached |
| later Save started | yes | no |
| terminal | completed | needs_decision |
| release verified | yes | yes |

The target saved SVG independently preserves a screen-equivalent24px x change.
The partial session's copied SVG remains at its initial x because Save never
starts. The postcondition sample spans are106.476ms and99.153ms. These are local
check intervals, not end-to-end or comparative speed measurements.

## Decision

Advance only to a fixed-context test of whether a model can author the patch,
target and tolerance from its presented evidence. Do not promote the operation
or apply it to OpenTTD: displacement covers moved objects, while road placement
needs a separate target-and-guard visual structure.

No model benefit, general task correctness, speed, token saving or cross-domain
claim follows.

Primary evidence:

- `results/local-displacement-postcondition-v1-probe.json`
- `results/local-displacement-x11-01/report.json`
- `results/local-displacement-x11-02/report.json`
- `results/local-displacement-x11-02/audit.json`
