# Second reproducible MAP01 threat fixture

`map01-threat-contact-v2` is the first and only outcome of the preregistered
model-free continuation from v1. It provides a different real-game state for the
v31 typed soft-history transfer test without depending on model navigation.

## Construction result

The shared X11 Executor loaded v1 at episode tic1263 and executed exactly two
programs: a compiled strafe-left / retreat-fire / strafe-right sequence, then a
750ms input-free coast. Both programs completed with verified empty key/button
release. No model ran. The child was saved at tic1366 and its exact source frame
hash differs from the v1 source frame.

Direct review of the saved source frame shows an enemy near the center, health
100 and ammo48. A fresh process validated the candidate manifest/save hashes,
loaded tic1366 exactly, and produced an exact first frame with the enemy still
visible, health97 and ammo48. The game runs continuously after load, so the
100→97 change before the first capture is retained rather than normalized away.
The hash-bound HUD reader independently extracts both health values.

The promoted manifest retains the parent manifest/save hashes and both parent
source/load tics. Session v8 is used only to chain setup fixtures; the frozen v7
session and all earlier results are unchanged. The fixture grants no runtime
input authority.

## Scope

The audit disposition is `PROMOTED_DISTINCT_THREAT_FIXTURE`. This proves a
reproducible state distinct from the exact v1 fixture with visible threat,
verified setup release, exact HUD health and fresh-process restoration. It does
not run v31 or establish gameplay, reliability, speed, token, or MAP01-clear
performance. The next allocation may use this fixture once to test whether a
soft event retained in one interval appears as the exact bounded summary in the
following existing planner turn.
