# Frozen Astra MAP01 attempt v1

Issue #58 requests a separately labelled Astra attempt for the real-time hero
showcase. This one-allocation gate keeps the same normal Freedoom 2 MAP01 visual
and OS-input contract as the Luna contingency work. Game time advances at 35
tics/second during model inference. The controller receives no game-state API,
automap, labels, action vector, pause, or save-state stepping.

The frozen allocation uses `gpt-6-astra` at low effort, seed 990609, skill 1,
four-turn persistent sessions, at most 56 decisions and a 600-second episode
limit. It retains the first outcome without rerun. A clean independently scored
map exit is hero evidence. Death, timeout, runtime failure or an unfinished run
is retained as-is and does not block the Research Preview. This is not a matched
model comparison and cannot attribute any difference to model identity.

The source hashes and full stop/retention rule are frozen in
`map01_astra_attempt_v1_prereg.json` before the first model call.

## Retained outcome

The single frozen run ended after 13 decisions and 149.911 seconds: MAP01 exit
false, player dead, one death and one kill. It crossed the first door, fought in
the lower area and reached later rooms, but did not recover from sustained
damage. Astra identified the final 0% floor-level view as death and returned no
commands. The independent clock probe measured 35.015 tics/second, so the game
did not pause. However, the fixed ten-second cover program expired before seven
of the 13 model calls returned. Those uncovered tails are a direct failure of
the intended continuous-local-control hero path, even though world time kept
advancing.

The run used 157,978 input tokens, including 93,440 cached input tokens, and
131.931 seconds of model time. It authored eight contingencies; none met the
conservative no-visible-effect condition. Thirteen primary program admissions
were recorded. One extra admission came from an internal contingency boundary,
not from a taken fallback.

This is a retained failed hero attempt. It is not rerun. The strongest observed
limit is sustained combat control and cover lifetime. The heuristic cover
program can end while the model still thinks, and its coarse movement/fire
choice is refreshed only at the next strategic decision. A useful next candidate
is renewable bounded cover with a model-authored policy for the inference
interval, including resource-aware fire and evasive movement, rather than a
DOOM-specific hidden-state hook.

The committed 78-second video contains the complete 149.9-second visual timeline
at labelled 2x playback, with model-thinking/local-cover and admitted-program
telemetry plus the unedited failure outcome. Run the audit with:

```sh
python research/doom/audit_map01_astra_attempt_v1.py
```
