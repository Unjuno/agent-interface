# Issue #59 T2 — callback state mutation follows delivered repeat events

## Result

`PASS_X11_CALLBACK_EFFECT_MATCHES_DELIVERED_KEYPRESS` (one candidate, one
independent raw-only audit, zero retries). In the stable-focus positive control,
window A's in-memory `movement_tick_counter` advanced 14 times during the held
W interval. In the focus-transfer condition, A's callback counted the initiating
press, focus moved to B while the global 32-byte keymap still marked W down, and
B's callback counter advanced from 0 to 15 during the 1.2-second held interval.
All 15 B counter increments linked one-to-one, in order, to distinct raw W
`KeyPress` events. Each effect row shows B as current focus, the complete keymap
with W down, and an exact `before=n, after=n+1` transition. Final per-window
counters were A=15 (14 positive + 1 transfer initiating press) and B=15.
Xvfb exited 0 and removed its socket and lock.

This extends T1's protocol receipt result by showing that a minimal client event
handler can mutate client-owned state on the new focus's later repeats despite
not receiving the initiating press. The counter is deliberately synthetic;
this does not establish any external application's useful or semantic effect.

## Frozen design and evidence

Allocation `ISSUE59-X11-CALLBACK-EFFECT-T2-20261002-01`; H/T/D/C/U and gates
are in `PLAN.md` and identities/limits are in `FREEZE.json`. Source main is
`8d9b496dd23b72bf73ca06756e23c329f5489735`. Pinned image
`map01-attack-onset-phase-a2:20260927-r2`, digest
`sha256:fc3022d265f465748e0a39491e28f8447d0066266e00d2a8a9144e866bf148ed6`,
linux/amd64 under OrbStack emulation. Container limits: no network, 1 CPU,
768 MiB, 96 PIDs, read-only root, no-new-privileges, and 96 MiB noexec/nosuid
`/tmp`. Existing shared container was not used or modified.

`results/formal-01/raw.json` retains 65 ordered X events, 8 full keymap samples,
7 focus/input actions, and every callback before/after state plus its linked
event id. The independent raw-only audit reports zero errors; 5 mutation tests
pass. `SHA256SUMS` covers frozen sources and formal outputs.

## Limits

The effect is one in-memory counter in a deliberately minimal X11 client, not a
real app/game's task state. The experiment uses private Xvfb and synthetic
XTEST only. It makes no claim about physical input, OS input authority, actual
game input, threat response, MAP01 progress/survival, safety, latency, or
efficacy. Counter mutation is not a useful-task-effect witness.
