# MAP01 first state-feedback and held-input timing join A01

Disposition: `PASS_SAME_RUN_CLOCK_JOIN_SCOPED` as a deterministic posthoc integration analysis. It is not a prospective/live allocation result.

## Question and method

The existing first-useful-feedback study timestamps independently reconstructed HUD health/ammo changes within admitted-program windows. The full-trace occupancy reconstruction bounds when any key was certainly held and when verified release had occurred. This A01 joins those two records for the same v39 trajectory using the common monotonic event clock. It first verifies the reconstructed feedback artifact ZIP and member hashes, then requires the feedback record's v39 report/events source hashes to equal the occupancy report/events hashes.

For each first feedback timestamp and each hold step in that same primary plan, classify it against the event-derived interval: before admission; during the admission/acknowledgment gap; through the last sample that confirms some key remains held; between that confirmation and verified release; or after release. No release time is inferred from a rounded duration alone.

## Result

Three admitted primary plans in the retained v39 run had a first independent health/ammo observation during the program. All three timestamps fell no later than the last sample confirming any key was still held for that plan's first hold step. The plan-3 observation (health 68→65, ammo 44→43) and plan-4 observation (ammo 41→40) coincide exactly with the retained confirmed-held endpoint. Plan-0 first observed ammo 48→47 at 233.889 ms after admission while its `Up + Shift_L + space` hold was inside its guaranteed any-key occupancy interval; its following `a` step began later.

This establishes temporal overlap in these three retained rows. It does not establish which key caused the HUD change, whether the change was useful or harmful, or whether the admitted action caused it. For plan 3 the same observation includes health loss. These are three plans from one stochastic episode, not three independent trials.

## H/T/D/C/U

- **H:** For the three v39 admitted primary plans with retained first HUD state feedback, that feedback was captured while at least one key from the associated action remained bounded as held.
- **T:** Read the immutable v39 occupancy result and decode the frozen #503 full-action archive; verify ZIP/member digests and the exact shared report/events identities; compare absolute monotonic nanosecond timestamps.
- **D:** `PASS_SAME_RUN_CLOCK_JOIN_SCOPED` if all three source-bound plan IDs reconcile, every hold relation recomputes from admission/ack/confirmed-held/release event stamps, and an independent audit agrees with the candidate output. The audit checks 3 plans, 5 hold rows, 3 guaranteed-occupancy feedback relations and zero errors.
- **C:** The observation may reflect world activity or a harmful event, and the action bundle contains multiple keys/steps. Temporal overlap alone cannot attribute cause or value.
- **U:** Retained evidence only; three plans in one trajectory; interval bounds rather than exact per-key release; no live run, model call, GUI, input, recovery-benefit, safety, human-tempo, or MAP01-clear claim.

## Execution and record quality

This was an exploratory deterministic posthoc computation, not prospectively frozen before the first candidate execution. The first candidate output and source identities are retained, and the independent auditor was run. Its first version stopped on an audit-assertion string mismatch before evaluating evidence; that audit STOP is retained. A one-line assertion correction was made, and the final independent audit passed without changing candidate code or result. This limitation remains part of the record.

See `RESULT.json`, `AUDIT.txt`, `SOURCE_SHA256SUMS.txt`, and `RAW_STDOUT.txt`. The exact source lines used to derive release bounds are in the retained current-main `audit_map01_held_input_occupancy_fulltrace_v4.py`.
