# V29 planner-authored typed cover validity

V29 integrates the model-free health signal and one-way validity guard into a
new controller candidate. It leaves v28 and all retained allocations unchanged.
No live model or gameplay allocation has run on v29.

## Contract

Schema v4 adds `next_cover_validity` beside `next_cover`. An active answer must
provide exactly one item with:

- `signal_id: "health"`;
- an absolute `hard_minimum` from 1 through 200;
- `max_source_age_ms` from 100 through 30,000.

The controller gives the planner the locally extracted current health, so the
planner does not need to transcribe that HUD value from the temporal sheet. The
condition belongs to the next cover. At the next admission, the runtime binds it
to a fresh exact observation, current window identity and capture time.

The runtime rejects cover commands when current health is already below the
authored floor. It also rejects an envelope that would absorb more than 20
health points from its fresh admission source. Rejection substitutes input-free
coast while the current planner obtains a new decision; the prior cover commands
receive no authority. The 20-point cap is a construction safety bound, not an
empirically optimal value.

If there is no prior authored cover, the first decision uses a conservative
local envelope whose hard floor equals current health. A health increase is a
soft event; any health loss invalidates that initial dependency. While an
authored envelope is active, distinct values at or above its floor are
coalesced and retained for the planner without stopping the existing cover.
Below-floor, unknown, expired, nonadvancing or binding-mismatched evidence enters
the existing one-way invalidation path.

That hard path interrupts the matching planner turn, sends `cancel` to the
current cover and requires a `cancelled` terminal with verified empty key and
button release. Its dependent answer and `next_cover` remain discarded. The
validity signal never grants input or proves task success.

## Model-free evidence

The v29 tests replay the retained v28 source at health 93 with an authored floor
of 80. Health 87 and 81 preserve existing authority as two soft events; health
79 hard-invalidates. A separate case starts below the authored floor and rejects
the prior cover, then uses the fresh source as the strict current-decision floor.
Another rejects a floor that permits more than the 20-point construction cap.

The cancellation boundary test verifies matching planner interruption, the
exact cover cancel command and mandatory empty release. Schema tests require the
singleton validity envelope for active answers, require it to be empty for a
terminal answer and reject zero as a floor. The complete relevant set passes 32
tests on Windows; the v29/signal/guard subset passes 15 tests under WSL/Linux.

## Remaining gate

This is committed construction only. It does not establish whether Luna chooses
useful floors, whether soft preservation allows a decision to finish, whether
the 20-point cap is appropriate, or whether gameplay, survival, latency, token
use or MAP01 progress improves. Before one live allocation, freeze the exact
model, effort, fixture, decision count, cap, output schema and acceptance rules.
Retain the first run even if the envelope is rejected, every turn is interrupted,
the player dies, or no progress occurs.
