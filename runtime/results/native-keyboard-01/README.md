# Keyboard continuation without an extra target click

The native self-use harness previously required a click at every action stage,
even when the primary assistant had already selected the object and only needed
keys. In Inkscape, clicking an already selected object can switch its selector
handles into rotation mode. The mandatory pointer movement/press also caused two
additional pointer guard captures.

## Integrated behavior

`NativeHandleBridge.keyboard(alias, offset, tail=...)` uses the same scoped visual
handle, lease, pre-admission guard, current-focus guard, native admission, terminal
release and sticky recovery rules as the click path. It compiles focus validation,
the explicit keyboard tail and release, with no pointer operations. The guarded
focus implementation only validates the already focused target; it does not
refocus it. Stale or unavailable context refuses, with no fallback click.

The existing exchange/harness accepts `interaction: "keyboard"`; default remains
`click`. The caller must still give the exact delivered `source_sequence` and
`point` used to mint a visual context anchor. For keyboard mode, that point is
not a pointer destination. The tail must contain explicit text/key input; empty,
wait-only and pointer tails refuse before admission. No new queue, background
worker or implicit plan is introduced. Batch-tail semantics are unchanged:
these are boundary guards, not per-key semantic re-grounding during the batch.

## Primary-assistant use

Fresh private WSL/Xvfb Inkscape seed 991100. The assistant viewed the source image,
clicked the object, then viewed the selected-object image. It chose keyboard mode
with 12 Right chords, a 50 ms pre-save wait and Ctrl+S. There was no second click
and no pre-movement click-settling wait in this keyboard batch. The final image
showed ordinary translation handles and x=74. Independent saved SVG parsing
confirms x=74 from x=50 (the goal was dx=24), y=50, width=40, height=30.

The actual keyboard program has zero pointer ops, 28 key emissions, two guards
(before admission/focus), and verified neutral release. Its required capabilities
do not include input.pointer. The preceding selection-click program has four
guards. This structural difference is not a matched latency comparison: the two
stages do different work. Three existing retired-alias click probes refused with
zero emissions; unit controls separately cover keyboard refusal/no fallback.
Finish was explicit at stage 3; all private processes were terminal at cleanup.

No sensor lane was configured or changed in this work. The user requested that
the primary assistant focus on integration/use and leave sensor development to
other contributors. Prior sensor and failure records remain unchanged.

## Evidence and limits

53 bridge/exchange/presenter/reference tests pass. New cases cover a pointer-free
program with required release, stale/recovery refusal without dispatch, and
invalid keyboard tails before admission. `audit.py` checks the raw programs,
emissions, guards, source/request/reply digests, image hashes, cleanup and exact
saved SVG. The local combined keyboard exchange time is in SUMMARY.json and
includes feedback/review and diagnostic stale-alias probes; it excludes model
reasoning and host transport. Human-tempo, token and causal speed gains are not
established. No helper model or Docker allocation was used.

Setup uses the unchanged caller route with fresh paths and newly grounded input:

```sh
PYTHONPATH=.:research/live_control python3 research/live_control/run_native_calc_self_use_v1.py \
  --app inkscape --max-stages 4 --probe-old-target --seed 991100 --out results-local/FRESH-DIRECTORY
```

Read-only evidence check:

```sh
python3 runtime/results/native-keyboard-01/audit.py
```
