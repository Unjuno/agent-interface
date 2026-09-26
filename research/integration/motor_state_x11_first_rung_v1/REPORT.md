# Issue #27 MotorState X11 first rung — formal result

Disposition: **PASS_MOTOR_STATE_DISTINCTION_SCOPED**. This is the first state-distinction rung only; Issue #27 remains open for task/planner usefulness.

## Frozen question

A command/receipt-only motor state can falsely confirm current motor state after external pointer displacement or focus transfer. A fresh OS/X-server readback should expose those mismatches, while unavailable observation must remain UNKNOWN rather than confirmed.

## Formal execution

Six prospectively frozen 3-case batches ran once each: Inkscape and Calc for repetitions 0, 1 and 2. All six outer invocations exited 0. Formal reruns/replacements/post-freeze tuning: 0/0/0. The source was publicly frozen before formal and GitHub-readback blobs passed an excluded 3+3 smoke first.

| result | count |
|---|---:|
| formal cases | 18 |
| held button/key state independently observed during gesture | 18/18 |
| neutral release at final scorer read | 18/18 |
| candidate MATCH | 6 |
| candidate MISMATCH | 6 |
| candidate UNKNOWN | 6 |
| command-only false confirmations after directed perturbation | 6 |
| command-only unsupported confirmations with observer unavailable | 6 |
| authority=none | 18/18 |
| feedback-specific input dispatch | 0/18 |

Inkscape stable cases ended at the commanded pointer and displacement cases ended at the independently injected pointer location. Calc stable cases retained the command-time X11 focus identity and focus-transfer cases ended at the mapped helper window. Observer-unavailable cases returned UNKNOWN; the independent scorer still recorded final server state.

The deliberately weak command-only comparator says MATCH in every case. It is wrong in all six directed pointer/focus perturbations and unsupported in all six observer-loss controls. This supports only the distinction that current observed motor state must not be inferred from command completion.

## Audit / evidence

The independent raw auditor imports no runner code and reconstructs all 18 rows with errors=[]. Ten copied-evidence corruption controls all reject. The six files under `formal/` are GitHub-readable semantic reformats. Byte-exact consumed `RAW.json` files are retained separately in `FORMAL_RAW_EXACT.b64`, bound by `FORMAL_RAW_EXACT_MANIFEST.json`; decoded archive SHA256 is `87656ef81afbbf544fdf3abbdc7f5a7bf3bf404df17c3518ec49e0234bdd73ce`.

Construction history is retained separately: initial Xauthority/Xvfb and focus/lifecycle failures remain STOP evidence; final GitHub-readback smoke passed 3/3 Inkscape and 3/3 Calc before formal.

## Scope

X-server pointer/key/focus state is not physical HID telemetry and is not proof of application effect. This allocation does not score Inkscape object displacement or Calc cell values, does not compare screenshot/receipt-only versus MotorState planner behavior, and does not measure correction boundaries, tokens, latency, cross-platform reliability or product readiness. Those are later #27 rungs.
