# Planner-facing patch servo — 2026-09-13

Candidate session_v16 and interactive_v13 expose `pointer_servo` as a single-step
program. The ready event describes required fields, nested point representation,
bounds and outcome meanings. This is a machine-readable descriptor with prose
constraints, not a complete JSON Schema or a schema for every inherited operation.

```json
{"op":"pointer_servo","source_sequence":1,"box":[592,369,56,44],"target_delta":[30,0],"points":[{"x":619,"y":390},{"x":631,"y":390}],"duration_ms":100,"max_corrections":3}
```

Submit using the existing program envelope with expected_sequence and original
valid_until_ns. Source sequence must be current at validation and execution; servo
must be the only step so earlier steps cannot invalidate its declared source.
All fields are validated before input, including source patch construction and
the inherited initial path/combined budget constraints. Correction count is 1..3,
target components ±32 px, per-correction cap 24 px. Parent guided execution allows
one further feedback opportunity to confirm the goal or report update exhaustion.

The worker services its own bounded replies from the declared patch policy through
unchanged owner_v9 authority. No remote reply is needed at intermediate yields.
`servo_feedback` retains tracking evidence and reason; `servo_outcome` reports local
goal separately from semantic verification. Lost/ambiguous/invalid/update-limit
outcomes return `needs_decision` after release, not `completed`. Exceptional expiry,
cancel or callback failure still follows executor terminal handling and may have
no servo_outcome; the terminal remains authoritative for execution status.

## Actual assistant use

The assistant viewed initial Inkscape image 001, chose the object-boundary patch,
center/initial path and target 30 px, and submitted one servo program. It then
viewed final image 005 and sent a separate save/settle program. No color detector
selected the assistant's command, and no remote pointer_reply commands occurred.
This is the same familiar single-object layout, not held-out perception evidence.

The program completed in 1,179.3 ms from acceptance to terminal, using two local
corrections. Saved XML independently gives 30.00000022 screen px at 118% zoom,
with y=50, width=40, height=30 and no transform preserved. Legacy score also passes.
The interval excludes initial assistant image inspection/planning, clock exchange,
save and scoring. Previous remote reply failure targeted 24 px and used a different
protocol; neither speedup ratio nor human-speed capability follows from these trials.
Full observations are still emitted: reduced remote correction boundaries do not
establish image/token reduction or retention robustness.

## Outcome regression

Two scripted actual-app cases replay original/unselected and selected-source
conditions. The former reaches 24 px; the latter reproduces tracking loss and now
terminates `needs_decision`, release verified, with zero saved displacement.
The latter's coarse setup still does not move the object, so it is a selection-state
case, not shifted-position coverage. This probe intentionally retains that failure
to check outcome mapping. No real distractor case has been run yet.

`audit_servo_interface.py` verifies 32 exact reconstructed frames, listed source
hashes, release states, outcome mappings and the assistant saved-object result.
Listed manifests are not exhaustive environment manifests. All entrypoint/probe
processes exited normally; separate per-child cleanup attestation remains absent.

## Remaining work

Selection-decoration sensitivity, real distractors/lost-target changes, timeouts
with the new synchronous callback, full operation schema and cross-domain cases
remain gates. Source sequence/frame labels do not prove atomic image freshness.
The callback still emits observations before correction, so blocked output can
consume the reply window; original lease/reply deadlines remain unchanged. Existing
manual pointer_reply is still available and is not an isolated private local-control
channel. No baseline promotion, freeze qualification, token saving or general servo
claim is made.
