# OpenTTD retained effect-state diagnosis, v1

## Result

The frozen seed991003 v6 episode did not complete the five-tile L objective and
did not emit its formal finish evaluation because of the retained driver race.
The source-pinned observer nevertheless continued writing independent task state
throughout the episode. A posthoc audit now separates those two facts.

The observer log contains263 records and exactly two unique guard states. Records
0..90 contain no target road. At index91, target tiles977,978 and979 become
company-owned road. The final172 records preserve that state. Tiles1043 and1107,
which form the B-to-C leg, remain empty; all four forbidden tiles remain clear
and every non-target guard tile remains unchanged. The full hard score is false.

The model submitted the same A-to-B drag on turns5,9 and11:

```text
(705,240) -> (673,256) -> (641,272)
```

It never submitted the distinct B-to-C drag. Thus the episode contains a stable
partial construction effect followed by repeated work over the same segment.
This narrows the failure from an unscored general failure to missed effect/state
progression plus an unfinished second segment. It does not prove which visual
frame first made the road leg recognizable to the model.

## Bounded visual evidence

`openttd_drag_effect_v1.py` derives a box from each drag path with20 pixels of
padding, then renders the fresh pre-action crop, final post-action crop and
amplified absolute RGB difference. The retained crops cover104x72=7,488 pixels.

| turn | before/after sequences | changed crop pixels | changed full-frame pixels |
| ---: | --- | ---: | ---: |
| 5 | 22 / 24 | 3,628 | 152,384 |
| 9 | 38 / 40 | 250 | 143,475 |
| 11 | 45 / 48 | 451 | 174,150 |

The first drag has a much larger local change than the two repeated drags. The
full frame is highly dynamic, and even the crop includes labels, cursor and game
animation. Pixel counts therefore remain presentation evidence only. Semantic
construction status comes from the independent observer audit.

Artifacts:

- `results/timing-envelope-openttd-l-06/posthoc-audit.json`
- `results/timing-envelope-openttd-l-06/drag-effect-audit.json`
- `results/timing-envelope-openttd-l-06/drag-effect-turn-5.png`
- `results/timing-envelope-openttd-l-06/drag-effect-turn-9.png`
- `results/timing-envelope-openttd-l-06/drag-effect-turn-11.png`

Both audits rebuild from frozen raw files, assert exact states, paths, sequences,
pixel counts and source hashes, and pass on Windows and WSL. This is one archived
diagnostic. A fresh preregistered live comparison is required before feeding the
crop to the planner by default or claiming fewer turns, tokens or elapsed time.

## Next interface test

For the next changed case, construct the action-region evidence immediately after
an accepted drag and present it beside the current full frame. Compare it with
the current full-frame path under the same model, task, seed and order-balanced
allocation. Gate every semantic effect with the independent task observer. The
candidate succeeds only if correctness is preserved and repeated already-complete
segment work, planner boundaries or measured tokens decrease.
