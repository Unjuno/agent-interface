# MotorState Calc application-effect rung — formal result

Issue: #27  
Allocation: `motor-state-calc-effect-27-20260923-01`  
Disposition: **PASS_MOTOR_STATE_EFFECT_GUARD_SCOPED**

## H/T/D/C/U

The prospectively frozen hypothesis was that a command-only continuation can route input to a wrong surface after focus transfer, while a fresh X-server focus observation can refuse that task input. Missing observation must remain UNKNOWN/refuse rather than become confirmation. Stable current-focus cases must still produce the requested Calc A1 effect.

Formal used LibreOffice Calc 25.2.3.2, private Xvfb, Python-Xlib/XTEST and a read-only scorer-only local UNO socket. Three scenarios × two policies × three repetitions = 18 fresh Calc/X-server lifetimes in three immutable six-case batches. Formal commands ran once each; reruns/replacements/post-freeze tuning = 0.

## Result

| condition | observed |
|---|---:|
| stable intended Calc A1=7 | 6/6 |
| naive focus-transfer wrong-surface effect (helper received 7, Calc blank) | 3/3 |
| observed-guard wrong-surface effect | 0 |
| observed-guard mismatch refusal | 3/3 |
| observed-guard UNKNOWN refusal | 3/3 |
| naive actions without fresh observer | 3/3 |

Every case independently exposed held Shift state, then neutral release, and ended X-server neutral. Candidate task input is zero in every mismatch/UNKNOWN case. Authority remains `none`.

The observer-unavailable comparison is an explicit liveness tradeoff: the naive arm happens to write the correct Calc cell in those three directed cases, but it does so without fresh observation support; the candidate refuses.

## Evidence

Raw SHA-256:
- rep0 `ab57e5f76404050521d3ed06c9f5d0e7011838a5b3c0da5bb0a03a8ea9deea20`
- rep1 `9f52fcd2ea01d3dd5adecac0f837b865c218f836b941c75a63236981f854207a`
- rep2 `9df718fa47acadd57ee0ff79d5b95beb0c925d2d55f952c80d31afd5f89c04d5`
- frozen audit `086505d0e4c63753f76117ae0fe0cef952880d75fd75690eaa83f2acebf42a72`
- controls `15f2cf1da6601503eddf1f6da8be52968ad6ea6a19ad9eb10d11ff8d2d4d0370`

Frozen independent audit reconstructs all 18 rows with errors=[] and all 10 copied-evidence mutations reject.

Post-result review noticed that the frozen audit did not aggregate child process exit receipts. The original audit is unchanged. A separate read-only audit v2 over the same RAW verifies 18/18 Calc teardown receipts (exit 255 after authored SIGTERM), 18/18 Xvfb exits 0, six expected Tk helper SIGTERM exits -15, and 12 absent helper processes; errors=[]. No scientific case was rerun.

Lossless evidence archive contains the three exact RAW files plus FORMAL_AUDIT.json and CONTROLS.json: 1,136 bytes XZ, SHA-256 `9edf64e81e928e3debf33ba77bfe533f890875a0880706e02a5c28940eefb6b9`.

## Scope

This establishes a finite application-effect boundary for one Calc action: fresh observed focus prevents the directed wrong-surface input that command-only continuation permits. It does not establish planner/model usefulness, screenshot reduction, latency/token benefit, natural focus-loss rates, Inkscape transfer, physical HID telemetry, cross-platform reliability, or product promotion. UNO is evaluator-only privileged state and grants no task authority.
