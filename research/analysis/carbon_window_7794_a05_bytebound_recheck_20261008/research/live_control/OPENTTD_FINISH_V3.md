# OpenTTD typed finish outcome and third fixed-Astra episode

Status: fresh positive and negative integration pass; same-task evidence only.

The second matched block exposed a boundary bug. When the model requested
verification but the independent engine score was false, the score was retained
while the driver raised an assertion before publishing a typed failure result.
The supervisor therefore saw only an unexpected driver exit.

## Candidate repair

`openttd_finish_outcome_v1.py` makes independent evaluation authoritative and
classifies three terminal paths:

| Trigger | Persisted outcome |
| --- | --- |
| Independent evaluation succeeds | `result.json` |
| The nine-turn bound is exhausted | `failure-evaluation.json` / `bounded_turn_limit` |
| A verification request receives a negative independent score | `failure-evaluation.json` / `visual_verify_false_positive` |

The v3 supervisor waits for either persisted success or failure. It reports a
negative independent score as task failure after the driver exits cleanly,
instead of translating it into an integration exception.

## Preregistered fresh validation

The first case launched a fresh canonical OpenTTD fixture, submitted no task
input and made no model call. It immediately requested independent evaluation.
As preregistered, the evaluator reported no target road, the driver exited zero,
and the typed negative outcome recorded `visual_verify_false_positive`, zero
durable input calls and zero executed proposals. This control validates the live
negative packaging path. Because no model judged the image, it is not another
observed visual-reasoning error.

The second case used the same v3 path for a normal fixed-Astra episode. Astra
requested independent verification after five action turns. All target,
connectivity, forbidden-row and surrounding-tile checks passed.

| Measurement | Fixed Astra v3 |
| --- | ---: |
| Initial observation to semantic completion | 92.377 s ±50 ms |
| Wrapper-observed model wait | 79.681 s |
| Proposal to useful feedback, five actions | 10.605 s total |
| Model calls | 6 |
| Reported input tokens | 97,729 |
| Reported output / reasoning output | 1,224 / 716 |
| Exact frames | 28 |
| Contact sheets | 3 |
| Durable calls / append records | 20 / 41 |

Provider receipt, provider first token, runtime receipt and exact OS injection
remain `NOT_RECORDED`.

## Cumulative same-task evidence

Fixed Astra has now passed this exact guarded road task 3/3. Completion times are
98.351, 94.929 and 92.377 seconds; their descriptive mean is 95.219 seconds.
Mean model wait is 82.092 seconds and mean reported input is 108,546 tokens.
The calls per episode are 7, 7 and 6.

This is repeated evidence for one known task and one prompt policy. It does not
establish performance on a different toolbar state, geometry or task, and the
downward sequence is not a learning or speedup result. Cache state, sampling and
generated action sequences differ.

Across the two matched blocks and this v3 validation, the retained artifacts now
contain 53 model calls, 192 durable calls and 299 exact frames, including the
one-frame negative control.

## Evidence

- Preregistration and raw artifacts:
  `results/timing-envelope-openttd-matched-03/`
- Audit: `results/timing-envelope-openttd-matched-03/audit.json`
- Audit command: `python research/live_control/audit_openttd_finish_v3.py`
- Artifact regression:
  `python research/live_control/openttd_finish_outcome_probe_v1.py`

The fresh audit checks source hashes, the zero-input negative path, all positive
model receipts, 29 exact frames, 20 durable calls, input release and independent
scores. It passes on Windows and WSL.

## Decision

Promote typed independent finish failure to the next experimental driver
semantics. Do not promote fixed Astra as a general route. The next OpenTTD
allocation must alter task geometry or initial toolbar state and retain the same
independent completion gate. Human comparison remains open.
