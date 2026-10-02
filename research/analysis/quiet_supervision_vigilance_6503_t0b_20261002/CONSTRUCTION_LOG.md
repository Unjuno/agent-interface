# Construction history — T0b (not formal experiment evidence)

This file preserves pre-freeze package-development outcomes. These commands
ran on host macOS arm64 / CPython 3.14.5; they did not invoke `run_candidate.py`
or `run_auditor.py`, Docker, OrbStack, WSLc, any human, GUI, or model.

## Attempt 1 — contract defects found

Command: `python3 -m unittest -v test_t0b.py`

Initial result: 10 tests, 8 passed, 1 failed, 1 errored. The full fixture audit
rejected its own first construction due to a periodic-checkpoint overlap with
the hard-stop event (only five discretionary C checkpoints), and its
independent scorer reconstruction disagreed on delay for a non-anomaly row.
The nested oracle-leak test also addressed a nonexistent payload field. Earlier
intermediate version of this attempt showed B/C schedule and evidence-schema
disagreement; its exact terminal result was `B_C_factual_field_schema_mismatch`,
`checkpoint_count_not_matched`, and `scripted_scorer_outcome_mismatch`.

Corrections before freeze: moved C's predeclared fixed windows to positions 4
and 10, made non-anomaly response windows explicit from the recorded event
time, repaired the nested corruption control, and counted the hard-stop alert
as an invariant overlay rather than a discretionary checkpoint.

## Attempt 2 — mutation control targeted a non-checkpoint

Command: `python3 -m unittest -v test_t0b.py`

Result: 9 passed, 1 failed. The fixed-schedule mutation targeted early position
3 after the schedule had changed to positions 4 and 10, so it was a no-op. This
was a test-target defect, not a candidate/material outcome. The control now
mutates the declared position-4 checkpoint.

## Attempt 3 — construction suite after initial corrections

Command: `python3 -m unittest -v test_t0b.py`

Result: 11/11 passed under `python3.12 -B -m unittest discover -s
research/analysis/quiet_supervision_vigilance_6503_t0b_20261002 -p 'test_*.py'
-v`. `py_compile`, JSON parsing, and `git diff --check` passed. The independent
host audit reconstructed 144/144 policy rows and 36 unique opportunities,
matched six discretionary B and six C checkpoints, verified one invariant
hard alert per policy, and reproduced the scripted hit, late miss, false alarm,
unobservable-event, and prompted-stop controls (139 scripted no-response rows,
one of which belongs to an unobservable anomaly; this is not human-response
data). Source/effect checks matched, with zero auditor errors. This remains construction
evidence only; the candidate/auditor CLI pair and container experiment are
unrun pending an explicit isolated OrbStack CPU/container assignment.

## Attempt 4 — visibility boundary and mutation-isolation regression

After clarifying that an uncaptured anomaly must be absent from every display
while remaining in the assigned denominator, a 12-test suite had one failure
when run in suite order. The new display-boundary case passed alone but failed
after the nested oracle-leak corruption control. Root cause: the candidate's
in-memory material row aliased the shared stimulus evidence dictionary, so the
negative-control mutation contaminated later tests' shared fixture. This is a
real construction defect; the candidate now deep-copies recorded evidence and
the regression explicitly asserts that output mutation cannot change input.
The uncaptured opportunity carries an empty evidence payload, no source
reference, and no human-visible row in any arm, but all four policy rows remain
in the denominator and the oracle classifies it as unobservable.

## Attempt 5 — final construction suite before allocation request

Command: `python3.12 -B -m unittest discover -s
research/analysis/quiet_supervision_vigilance_6503_t0b_20261002 -p 'test_*.py'
-v`.

Result: 13/13 passed. The sparse worktree has all 533 retained directory names
indexed in `research/analysis/README.md`; the local checker's sparse-checkout
metadata probe does not recognize this linked-worktree layout and prints a
stale warning while returning 0. This is not a clean local index PASS. In the
official CI's sparse checkout that probe recognizes absent siblings as sparse
and permits them. `git diff --check` passed. The independent host reconstruction
retained 144/144 rows, 36 opportunities, six B and six C checkpoints, one
mandatory stop in each arm, and the planted scoring controls. All response
fixtures are marked `synthetic-script`; no human-response row exists. The
candidate/auditor CLIs, container, and formal T0b experiment remain unrun.

## Attempt 6 — local CI-equivalent regression suite

Ran all 18 test commands currently listed in `.github/workflows/analysis-index.yml`
under CPython 3.12, for 117 tests total. All passed, including the #6590
geometry-feasibility suite after locally applying its workflow's pinned-source
restore step; without that step, two existing provenance-hash tests correctly
failed because the current workflow source is intentionally different. The
branch workflow was restored and verified byte-for-byte against `HEAD` after
that test. `py_compile` and the #6503 13-test suite passed. These are local
construction/regression checks, not the formal candidate/auditor experiment;
no candidate/auditor CLI, container, human, or model was invoked.
