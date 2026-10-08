# MAP01 preplanned local contingencies

Command-effect receipts arrive much sooner than a new model plan. In the prior
40-decision compact run, a `no_visible_effect` receipt reached the next
model-authored plan after 8,682.54 ms median. This experiment lets the same model
attach a bounded fallback to a primary semantic command. When that command has
no visible viewport effect, the controller skips its remaining primary tail and
submits the fallback locally without another model call.

The condition remains deliberately narrow. It is normalized viewport pixel MAE
at or below 0.015, derived from exact samples already emitted during the held
input. It does not claim collision, door state, damage, hidden position, or task
failure. The responder avoids attack-hit contingencies and asks for them only
when an effect is expected and a safe fallback is clear.

## Live normal-game result

Two sequential 12-decision Luna-low runs used normal Freedoom 2 MAP01, skill 1,
seed 990609, continuous `ASYNC_SPECTATOR` time, and four-turn model sessions.
The initial viewport descriptor MAE was 0.00000272, far below the 0.015
no-visible-effect threshold. The IWAD paths differed after
the local runtime dependency was restored, while their SHA-256 hashes matched.

| Controller | Authored contingencies | Taken | Branch ms | Admissions | Extra vs one bundle/decision |
|---|---:|---:|---:|---:|---:|
| every command split | 6 | 1 | 111.50 | 18 | 6 |
| contingency-boundary grouping | 4 | 1 | 95.33 | 13 | 1 |

In the grouped run, `use` produced `no_visible_effect`; a preplanned
`backward short`, `strafe_left short` fallback was accepted 95.33 ms after the
effect sample. The prior 8,682.54 ms median model path is about 91 times longer,
but that comparison uses three earlier model-path events and one new local
branch. It establishes removal of the model round trip from this path, not a
population speedup estimate.

The first implementation submitted every semantic command separately. The
grouped controller bundles commands until a contingency boundary and bundles
the fallback as one program. It reduced admissions from 18 to 13. Its only
admission above one primary bundle per active decision was the fallback that
actually ran. Existing effect sampling remained nearly unchanged: 66 samples
and 234.56 ms total capture in the split run versus 66 and 232.25 ms grouped.

Both runs remained unfinished with zero deaths and kills. Total wall time was
100.50 s split and 106.63 s grouped, while model time was 86.68 s and 92.40 s.
Model latency dominates and outputs are nondeterministic, so these sequential
runs do not support a wall-time or gameplay-quality claim. Completion, false
branch rate, and longer-horizon recovery still need measurement.

The first schema attempt omitted the required JSON-schema `type` beside
`const`; it failed on the first model call with no input program admitted. Three
later environment starts failed before play while restoring a reproducible
ViZDoom/Pillow path. Compact failure receipts are retained with the result.

Run the repository-backed audit with:

```sh
python research/doom/audit_map01_contingency_v1.py
```

The committed record contains reports, independent scores, environment data,
source frames, filtered plan events, contact sheets, exact controller/schema/
responder sources, and compact failure receipts. Full streams remain under
`results-local/doom`.
