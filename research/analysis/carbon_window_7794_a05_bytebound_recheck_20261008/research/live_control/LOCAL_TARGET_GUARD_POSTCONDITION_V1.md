# Local target-and-guard postcondition v1

## Purpose

Object displacement is insufficient for placement tasks. This candidate compares
an immutable source frame with fixed, disjoint target and guard boxes. Every
settled sample must contain at least the declared target change and no more than
the declared guard change. It can gate only later steps already admitted in the
same bounded program.

The result explicitly sets semantic verification, task success and new-input
authority to false. An independent application scorer remains above it.

## Archived OpenTTD feasibility

Development images from runs2/9/10/11 fixed a24-channel pixel threshold,120
changed target pixels and at most20 changed guard pixels. A separately
preregistered v6/v7/v8 set first failed4/6 because two first samples preceded the
persistent road effect. V7 changed from12 to169 target pixels; v8 changed from a
13-target/36-guard transient to170-target/0-guard. This rejects pre-settle
sampling.

The runtime contract now requires a bounded `settle` immediately before the
condition. Without changing boxes or thresholds, a settle-aligned archived
allocation passes6/6:

- three independently diagnosed first road segments return `met`;
- two repeated completed-segment drags return `target_not_reached`;
- a later second road segment inside the first condition's guard returns
  `guard_changed`.

This is offline visual feasibility. The archive uses later observations as a
settle proxy and therefore does not establish live OpenTTD timing.

## Fresh X11 integration

The first target/partial/guard order retains an immediate target focus
interruption with verified release. Its partial and guard branches pass. A
separately preregistered reversed order then passes3/3:

| Case | Visual result | Target changed | Guard changed | Save |
| --- | ---: | ---: | ---: | --- |
| target | right24px |84 |0 | started |
| partial | right20px |0 |0 | stopped |
| guard | up20px |0 |450 | stopped |

The three sample spans are90.828--95.403ms. Exact frames, saved SVG state, source
identity and input releases audit on Windows and WSL.

## Decision

Retain the operator and advance only to a fresh OpenTTD allocation with bounded
settle and the existing independent engine scorer. Current boxes are human
authored, pointer paths are scripted and the fresh application is Inkscape. No
semantic success, generalization, speed or token claim follows.
