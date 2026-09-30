# T0 v2 — event-kind correction

This successor revision responds to an overclaim gap found during review of T0 v1: the scorer's effect category was constrained, but the source event kind was not. v2 requires `event_kind == TASK_EFFECT` in addition to the independently supported effect kind `KILL_COUNT_INCREASE` or `MAP_EXIT`. v1 freeze/result/raw remain preserved in the parent directory.

H/T/D/C/U and exact source identities are in `FREEZE.json`. 11 tests passed; 14 synthetic rows were audited in a separate Python subprocess with errors=0; 7/7 corruption controls rejected. This is synthetic construction evidence, not a live effect/recovery result.
