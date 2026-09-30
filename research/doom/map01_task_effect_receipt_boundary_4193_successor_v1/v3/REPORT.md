# #4193 retained-source schema compatibility v3

**Disposition: `HOLD_NO_POSITIVE_SCORER_EVENT`.** The retained source supports a native physical receipt join for 3/3 attack sessions. It contains no positive independent scorer endpoint in 0/3 attack sessions (and 0/3 no-input sessions). This is a read-only reanalysis of the original immutable source, not a rerun, replication, or live intervention.

## Findings

- 3/3 attack sessions have confirmed physical DOWN and UP brackets with native press/release IDs. DOWN and UP adapter edges agree on actuation ID; bracket and adapter-edge owner, intent token, key, and intervals match.
- The six session streams contain 196 independent progress samples (32, 32, 34, 32, 32, 34 in sorted session order); timestamps are strictly increasing within each session. They are not compared across sessions.
- All attack samples retain kill count 0 and map_exit false. No attack sample has a kill-count increase from its session baseline or a false-to-true map-exit transition. The no-input streams also have no positive endpoint.
- The producer schema does not provide `source_event_id` or `scorer_event_id` in these retained event records. A scorer endpoint locator can only be derived from session key, array index, `sample_ns`, and endpoint kind when a transition exists. The synthetic v2 event-ID contract is therefore not producer-compatible as a claim about native source fields.
- The fixed original session schedule binds the one recorded actuation per attack session. This does not establish a general multi-actuation plan-to-receipt join or bounded recovery result.

The canonical machine record is [RESULT.json](RESULT.json); reproduce it using [PLAN.md](PLAN.md), [runner.py](runner.py), and the independent raw-only [audit.py](audit.py). The predecessor #4193 frozen result is unchanged.
