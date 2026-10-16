# Identical emitted operations, different saved effect

Retained native-target-recovery-01 and native-multiapp-integration-01 both
compiled the identical 12-operation program: focus, pointer move, click press/
release, six Right chords, Ctrl+S, release_all. Both receipts report completed
operations 0..11 and 19 emissions, with verified empty held-input state.
The saved SVGs nevertheless contain x=60 and x=62 respectively (initial x=50).
Both retain y50/width40/height30/no transform and pass their directional task.

This is an application-effect discrepancy, not proof that the backend dropped a
particular key. The backend synchronizes X requests; its completion receipt is
not an acknowledgement of each application update. Different application sets,
source commits, initial interactions and execution context confound a causal
comparison. Text-gap configuration differs but neither program contains text;
the compiled operations are byte-for-byte equivalent after JSON normalization.
We have not identified whether selection readiness, repeat processing, scheduling
or another mechanism explains the difference. Do not label either run an exact
six-step success, or replace their original directional evaluation with failure.

## Next bounded comparison, not yet executed

Use one fixed source/environment/app/seed and record initial geometry and all
images. Separate selection-only input from keyboard-only input; the primary
must inspect selection before issuing six Right keys and save. Compare that
with the existing combined click+six-Right+save sequence in fresh allocations,
one allocation at a time, with alternating order and multiple repetitions.
Keep repeat count and text pacing fixed. Record saved displacement as well as
directional pass, emissions, release state and dispatch/feedback times. Include
all runs and failures. Selection-only creates an extra decision/image boundary;
measure that cost rather than calling it a speed improvement.

Only if the discrepancy persists with established selection should a second
comparison explicitly insert existing wait_update operations between chords.
Do not add implicit delays, change default pacing, or claim an exact keyboard
gain from these two retrospective samples. No sensor or helper model is needed.

Run audit.py to reconstruct report.json from frozen files. The audit reads
saved files after completion; it must not supply hidden geometry to live GUI
decisions. The report is not an additional live trial.
