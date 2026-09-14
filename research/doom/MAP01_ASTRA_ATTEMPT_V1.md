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
