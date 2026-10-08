# V39 hard invalidation and health recovery during cancel — A01

## H / T / D / C / U

**H.** Once current-main V39 has issued a paired-signal hard policy invalidation for an active cover, a later health recovery received while waiting for that cover's cancel terminal must not restore the old cover or make its pending planner answer admissible. The recovered full observation may still become the source for a fresh plan.

**T.** Freeze `origin/main` commit `743ae74ec5be2472ff27fa06fe13d5ecf8534de5`, the current V39 controller and `observable_signal_guard_v2.py`. Run an inert local construction with source health 100, hard floor 88, typed health 80 at sequence 11, then health 96 at sequence 12 during the exact production nested `wait()` call that waits for the matching cover terminal with `observation_monitor=None`. Require the verified empty cancel terminal, process the recovered full frame at the answer-boundary drain, and return a deliberately answer-eligible completed planner result. Gate that result through the production final-admission function. An independent auditor recomputes source hashes, thresholds, event order, empty release, fresh-source receipt, and rejection; three altered-result mutations must be rejected.

**D.** `PASS_SCOPED_REPLAY`. The real guard returns `HARD_INVALIDATED` at health 80 and `SOFT_CHANGED` at 96 against the original 100 baseline. The cancel wait does not feed recovery sequence 12 through the old cover monitor; the full frame at 12 is retained for new planning after the cancel terminal. The fake planner's answer remains eligible, yet production final admission returns `REJECTED_POLICY_INVALIDATED`, with no Executor admission or input authority. Executor cancel precedes planner interrupt in the composed trace. Candidate passes normally and under `python -O`; the independent audit passes eight assertions and rejects three result mutations. The preexisting 40 paired-monitor/drain tests also pass (their 20 drain tests plus 20 dual-signal tests).

**C.** Typed values and the planner are fixtures; no live OCR/capture timing or App Server behavior is represented. Event ordering is deliberately selected to exercise recovery during cancel wait. The verified-empty terminal is a fixture contract receipt, not physical key-up evidence. Prior V39 queued-invalidation and recovery-to-replan compositions cover adjacent properties but not this exact recovery-during-cancel-wait / still-ineligible-answer conjunction.

**U.** This does not show a threat was detected from screen pixels, how often the recovery event could be missed, actual per-key release, useful feedback, bounded live recovery, ammo/progress impact, or a Doom/MAP01 outcome. The live-game lane remains unassigned; this does not authorize or replace that exposure.

## Frozen inputs and reproduction

Production inputs: `research/doom/map01_overlap_controller_v39.py` SHA-256 `51ceed1ee329da2c64cf26300acddcf3e57b03ad8b193716709dcc0a95143607`; `research/live_control/observable_signal_guard_v2.py` SHA-256 `7be055c4bd68a1528f4b2b02b543435bd64465ea42d4452f5597d6dce08442a0`. Repository source commit: `743ae74ec5be2472ff27fa06fe13d5ecf8534de5`.

From repository root on Windows PowerShell:

```powershell
$env:PYTHONPATH = 'research/doom;research/live_control'
py -3.11 research/doom/v39_hard_recovery_pending_a01_20261009/run_experiment.py
py -3.11 -O research/doom/v39_hard_recovery_pending_a01_20261009/run_experiment.py
py -3.11 research/doom/v39_hard_recovery_pending_a01_20261009/audit.py
py -3.11 -m unittest research.doom.test_map01_v39_pending_observation_drain research.doom.test_map01_overlap_controller_v39_dual_signal -v
```

All executed stdout, stderr, exit codes, raw normal/optimized candidate results, audit output and SHA-256 inventory are in `results/` and `SHA256SUMS.txt`. An initial harness extraction error and a fixture-assumption failure were retained in `results/initial-attempts.md`; neither reached or modified production code.

## Additive audit correction (2026-10-09)

The original `audit.py` and its saved output are preserved as historical evidence. Independent review found that v1 reports `PASS_SCOPED_REPLAY` even when the saved candidate's final admission is changed to `READY_FOR_ACTION_VALIDITY` or `input_authority_admitted=true`. Use `audit_v2.py` for the corrected persisted-raw audit; it directly verifies all final-admission fields and counts the unique checks it executes. Its normal candidate passes 11 assertions, and `test_final_admission_audit_v2.py` verifies that both known false-pass mutations fail. This remains a scoped fixture replay with the live limitations above.

```powershell
py -3.11 research/doom/v39_hard_recovery_pending_a01_20261009/audit_v2.py
py -3.11 -m unittest research.doom.v39_hard_recovery_pending_a01_20261009.test_final_admission_audit_v2 -v
```
