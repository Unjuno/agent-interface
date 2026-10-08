# #1888 MAP01 loaded-fixture timeout precondition

Task: `MAP01-TASK-EFFECT-FIXTURE-TIMEOUT-PRECONDITION-R0-20260919-001`

Corrected preformal H: for exact retained `map01-threat-contact-v2` at episode tic 1366, a loaded episode is immediately terminal iff `episode_timeout_tics < 1366`. Equality is nonterminal. Session seconds39 ->1365 is therefore invalid; seconds40 ->1400 is valid.

T: six fresh DoomGame instances; load/read only; no action/advance/input. Exact fixture save, IWAD and ViZDoom version are checked at runtime. One formal invocation, reruns/replacements/tuning0.

D: PASS iff all six rows load at tic1366, observed `episode_finished` matches `<1366`, exact directed cases match, no player death/counter mutation, and source/audit integrity pass.

C: only a loaded-fixture/scorer precondition; does not establish task effect or physical lineage.
U: no recovery efficacy, task input, model, token, human-tempo, or production claim.
