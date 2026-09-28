# Hardening audit — 2026-09-28

Scope: repairs selected from the pre-repair benchmark-validity audit. This is benchmark-instrument evidence, not Agent Interface performance evidence.

## Defects repaired

1. **Target semantic ambiguity** — target color+shape is now unique among all moving objects. A 10,000-seed audit at 64 objects found 0 semantic collisions.
2. **Watcher blind polling** — clicking an inactive watcher is a forbidden action and terminates the episode. A controller cannot satisfy monitoring by sweeping fixed tile coordinates.
3. **Wrong-target / click-search shortcut** — wrong objects fail as `forbidden_action`; empty-world clicks fail as `motor_miss`.
4. **Realtime elapsed-time loss** — `ow_step(dt)` consumes the complete external `dt` using bounded 1/120 s internal steps. `ow_step(1.0)` advances exactly 1.0 simulation second in the control audit.
5. **Silent event-ledger truncation** — capacity increased to 4096 and overflow is explicit `instrument_event_overflow`. A 200-alert ACK stress records >=400 events without overflow.
6. **Impossible difficulty combinations** — cross-parameter validation rejects required alerts without watcher/event capacity and rejects insufficient event budget. Watchers can be explicitly disabled with zero required alerts.
7. **Framebuffer pointer feedback** — software cursor is rendered for panel/HUD interactions, so framebuffer-only mediation does not depend on an external X cursor.
8. **Fixed-layout specialization pressure** — seed selects one of eight map topology transforms; player spawn, station placement, and assembly piece/slot arrangement vary deterministically by seed. Assembly semantics are unique within the board.
9. **Failure attribution** — report now distinguishes episode timeout, missed alert, forbidden action, motor miss, terminal bad submit, assembly miss, and instrument event overflow; it also records wrong/motor/false-ACK counters.
10. **Container default execution** — runtime image owns an Xvfb server through `xvfb-run` rather than assuming an external `DISPLAY`.

## Construction controls

`make clean all` under `-O2 -std=c11 -Wall -Wextra -Wpedantic` completes with no compiler warnings.

`./test_ops_world`: **14/14 hardening tests PASS**.

The test suite covers:

- independent range validation plus cross-parameter feasibility;
- deterministic replay;
- seed-varied map/assembly families;
- target semantic uniqueness over 1,000 seeds at 64 moving objects;
- 64 watchers + 64 objects + 16-way burst generation;
- terminal success and bad-submit fail-closed control;
- assembly success and miss fail-closed control;
- alert ACK, deadline miss, and inactive false-ACK control;
- wrong-target and motor-miss fail-closed controls;
- target relocation/reacquisition effect;
- one-second realtime catch-up equivalence to 120 fixed substeps;
- 200-alert event-ledger stress without truncation;
- nonempty rendering plus framebuffer pointer cursor;
- exact reset/replay hash.

Independent post-test audit:

```text
semantic_collisions=0/10000
map_variant_mask=0xff
blind_spam_done=1
blind_spam_failure=3 (forbidden_action)
false_acks=1
catchup_sim_time=1.000000
internal_steps=120
```

## Post-hardening instrument cost

64 moving objects + 64 watcher tiles + 12 assembly pieces, alerts disabled for the no-controller render benchmark:

```text
10,000 / 10,000 frames
0.924507 s
10,816.57 frames/s
0.0925 ms/frame
max RSS 2,064 KiB
native binary 56,264 bytes
```

100,000 seeded resets with the same 64-object/64-watcher capacity:

```text
0.403393 s
247,896.91 resets/s
4.034 us/reset
```

These are local diagnostic measurements, not portable performance claims.

## Remaining HOLD gates

The repairs remove the concrete shortcuts found in the audit, but formal benchmark promotion still requires:

- hardened framebuffer/HID mediation and evaluator-private seed/report channel;
- automatic paired B0/C1 execution with fresh hidden seeds after candidate freeze;
- held-out generator/presentation families beyond the public eight-map transform family;
- repeated parameter-frontier allocation with uncertainty reporting;
- external model/image/token/cache/resource accounting;
- independent real-application/domain transfer evidence.
