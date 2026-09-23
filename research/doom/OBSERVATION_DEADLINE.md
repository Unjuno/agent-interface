# Observation timestamps remove a clock round trip, not the planner gap

The declared `observation_deadline_plan.json` was written before self-use seed
990601. The unchanged v7 runtime already emits capture_ns in its own clock.
For each new input the assistant used the latest sequence and
`valid_until_ns = capture_ns + 25_000_000_000`, instead of requesting the current
clock and extending validity from that later time. No host-clock conversion or
automatic renewal occurs. This is a client usage pattern, not a new runtime API.

The 25-second window is a deliberately generous exploratory bound for this
basic-room trial. It includes decision, transport and execution, and is NOT an
acceptable freshness budget for general dynamic gameplay. A latest sequence can
still be old. Runtime sequence, focus and expiry checks continue to apply; they
do not prove the visual evidence is semantically fresh or complete. If the window
has expired, re-observe under a new read-only intent; never renew old input merely
because a later clock response exists. Recovery may require a clock request.

## Actual self-use result

In `observation-deadline-01`, the assistant inspected 001.png and made a 250 ms
Left turn. The target moved to the right of center in 004.png, so it corrected
with a 60 ms Right turn and a 350 ms Space hold. It inspected the FINISHED screen
in 009.png, then ended control. Post-control score: finished and alive, reward98.

- Zero clock commands, two accepted programs, no rejections, eleven exact frames.
- Raw/delivered events match; every terminal and owner close verifies release.
- Initial capture to first acceptance: 12.429 s.
- Interval between acceptances: 22.347 s.
- Observation ages at input receipt: 12.415 s and 21.958 s.
- Remaining deadline budgets at receipt: 12.585 s and 3.042 s.

The old `shared-assistant-02` trial sent three clock commands (one after viewing
the finish screen), with intervals 20.468 s and 20.974 s respectively. Seeds,
aiming behavior and learning differ, so this is not a matched speed comparison.
The longer second interval in the new trial is direct evidence that removing
clock requests does not by itself solve the tens-of-seconds loop. Do not present
the faster first interval as a causal percentage gain. No actual token use or
client/model receipt timestamps are available.

## Audit and decision

Run `python research/doom/audit_observation_deadline.py`. It checks source hashes,
PNG/transport reconstruction, all submitted deadlines against their already-seen
observation, zero clock commands, cleanup and successful final scoring. It also
checks the existing Lease at deadline-1 ns and exactly at deadline with a
deterministic clock. This is not a late-input GUI stress trial. The captured
plan hash identifies the preregistered usage rule; full environment/model
qualification remains incomplete.

Decision: retain as an optional documented client pattern; no architecture or
performance promotion. The next speed study needs fewer model/tool boundaries
and actual endpoint instrumentation, while preserving full observations and
input authority. In particular, combine image delivery with action results and
separate backend image-ready, tool return, model decision and next submission
before choosing an optimization. The black-screen root cause, broader domains,
freshness budgets and Research Freeze qualification remain open.
