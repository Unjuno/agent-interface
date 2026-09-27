# Construction history

All work below occurred before source freeze and formal-01. It is exploratory and does not count as a formal allocation. Each pilot has its own output directory and is preserved as-run.

1. **pilot_01 STOP:** harness looked up a nonexistent Python-Xlib reply key `class`; the API names it `win_class`. No layout or candidate check occurred.
2. **pilot_02 STOP:** receiver control passed on all rows (InputOnly class/focus and exact `a` press/release), but an incorrect `xkbcomp` argv yielded an empty map dump, so the runner stopped before candidate delivery.
3. **pilot_03 exploratory runner PASS / auditor HOLD:** all four runner rows delivered the exact formula and passed controls. The first auditor rejected valid modifier-chord event ordering because its assertion was too simplistic; raw remains unchanged.
4. **pilot_04 construction PASS:** corrected audit independently checked the full press/release keycode trace, xev/XLookupString logs, XKB evidence, source hashes, zero-event refusal and held-key release. Audit returned `PASS_INDEPENDENT_AUDIT`; three corruption challenges passed with `raw_unchanged=true`.
5. **pilot_05 command STOP:** redundant `python3` conflicted with the image's Python ENTRYPOINT; runner did not start.
6. **pilot_06 STOP/HOLD:** the corrected invocation reached all cases, but three DE rows hit a stale `map_events` variable; the auditor also raised on null fields in STOP rows. No candidate claim is taken from this partial pilot.
7. **pilot_07 candidate PASS / audit HOLD:** all four rows delivered as planned, but the runner omitted the pre-candidate event snapshot on the US control; audit caught the missing field.
8. **pilot_08 construction PASS:** all four rows passed candidate, receiver, XKB, event-state, refusal and cleanup checks; independent audit reported zero errors; the wrong-decision, missing-case and altered-log corruption controls were rejected, with source raw unchanged.

The planned formal-01 invocation was intentionally **not run**: a concurrent GitHub branch for the same Issue #3794 hypothesis and exact intended path was discovered immediately before formal start. See `STATUS.md`. Construction PASS/STOP/HOLD records are not formal evidence and do not alter #3789's formal STOP.
