# A passing pre-input sample does not bind the later keyboard target

The frozen v2 modal guard accepts a correct Calc format dialog, but a test-only
focus mutation after that check makes the same ordinary Return activate ODF.
Executor reports `completed` with verified release while the requested XLSX save
has not happened. This is a retained counterexample, not a guard fix.

## Evidence

`probe_modal_check_input_race.py` writes its plan before starting two private
Linux/X11 Calc sessions. Both use seed 991022, values 532/590, the same frozen
template and guard, and ordinary Executor admission and a two-second lease.
An interposition at `session_v16.Backend.execute` runs after v2 revalidation.
The negative sends two setup-driver Tab keys there; the control sends none.
Both retain a pre-Return image before calling ordinary execution. No production
guard source is edited, and the interposition is restored during cleanup.

| Case | Guard / terminal | Saved XLSX A1 / A2 | Check to ordinary execute |
|---|---|---|---|
| Control | pass / completed | 532 / 590 | 6.299 ms |
| Post-check selection change | pass / completed | empty / empty | 38.718 ms |

Both cases retain unchanged X11 surface/focus/geometry across the mutation.
The negative pre-Return image visibly selects **Use ODF Format**; the after image
shows **Save as**, with **ODF Spreadsheet (.ods)** selected. The original XLSX
remains valid XLSX with empty cells. There is no evidence of a completed ODF save.
Independent artifact scoring reports false for the negative, true for control.

`audit_modal_check_input_race.py` checks listed source hashes, four exact public
AIT/PNG frames, sample predicates, time order, unchanged bindings, verified
release, and saved workbook values. Both guard images match the template; the
negative pre-Return action-region error is 0.118755, which would abstain if
sampled at that moment. Results and six diagnostic images are retained under
`results/modal-check-input-race-01`; the audit records image/artifact hashes.

## Interpretation and next architecture decision

This directly falsifies atomic target binding for this candidate. It does not
measure natural race probability: explicit fault interposition, two Tab events,
30 ms settling and an extra screenshot deliberately enlarge the check/input
window. Timings include instrumentation and are not a runtime speed benchmark.
The source manifest covers listed files, not every transitive dependency.
This is scripted DEVELOPMENT_KNOWN evidence, not live assistant performance.

Repeating a pixel check later can narrow this window but cannot by itself make
sampling plus X11 keyboard dispatch atomic. Issue #45 target handles therefore
need a stated target-consistency limit; a handle must not imply atomic binding.
Issue #34 effect verification remains necessary: `completed` means the bounded
program ended, not that the requested application effect occurred.

Next compare target-addressed activation with keyboard activation under this
same focus mutation, then introduce movement/occlusion so a coordinate route is
not credited merely for passing the keyboard-specific fault. Require separate
post-action verified/contradicted/unknown evidence and include its delay in the
boundary comparison. Do not promote this guard, auto-retry the failed save, or
grant freeze credit based on the two runs.

Run once (fresh output directory required), then audit:

```sh
python3 research/live_control/probe_modal_check_input_race.py
python3 research/live_control/audit_modal_check_input_race.py
```
