# Compact planner evidence: fixed-image decision comparison

The current live caller can attach complete durable state, continuation hashes,
raw program replies and checkpoint metadata to the next model decision. That is
excellent audit evidence, but much of it repeats transport state the caller has
already validated. This experiment asks whether a typed planner view can retain
the decision-relevant boundaries while sending fewer tokens to the model.

The compact view retains the saved-effect status and contract, actual value when
available, UNKNOWN reason, original query ID, digest for VERIFIED evidence,
whether the observation window remains open, task-score status, next-step rule,
authority and automatic-retry policy. For prior GUI execution it retains action
IDs, terminal status, completed/total steps, empty verified release, tail
submission and the explicit statement that the application effect is unknown.
Raw evidence remains in the caller and experiment archive.

## Fixed comparison

`compact-evidence-decisions-01` contains 16 predeclared model calls across four
archived live states. Each state has two calls with full evidence and two with
compact evidence. ABBA/BAAB ordering is balanced per case. Within each case, the
screenshot, task/schema prompt, model request (gpt-5.6-luna / low) and responder
instructions are identical; only the evidence JSON changes. No proposed action
executes.

The cases cover:

- Chromium before form input: UNKNOWN must lead to one exact-value submission.
- Chromium after form submission: VERIFIED plus visible confirmation must lead
  to verification, with no resubmission.
- Calc with a visible format dialog after interrupted Save: UNKNOWN must lead to
  a click-only confirmation, with no new Save.
- Calc after the dialog: VERIFIED plus visible A1=480/A2=192 must lead to
  verification, with no further input.

All 16 calls produce the expected decision. Full and compact conditions each
score 8/8. Neither condition proposes an extra Save. This is encouraging but is
only two samples per mode and case; it is not a reliability bound.

| Fixed state | Full evidence bytes | Compact bytes | Input tokens per full call | Per compact call | Saved per call |
| --- | ---: | ---: | ---: | ---: | ---: |
| Chromium UNKNOWN | 958 | 621 | 9,727 | 9,614 | 113 (1.16%) |
| Chromium VERIFIED | 1,509 | 684 | 9,899 | 9,653 | 246 (2.49%) |
| Calc UNKNOWN + dialog | 3,529 | 1,328 | 10,661 | 9,957 | 704 (6.60%) |
| Calc VERIFIED | 1,481 | 594 | 9,995 | 9,716 | 279 (2.79%) |

Across eight full and eight compact calls, reported input drops from 80,564 to
77,880 tokens: 2,684 total, or 335.5 per call and 3.33%. Input counts repeat
exactly within every mode/case pair. This isolates prompt token count better than
runner time. The screenshots and common instructions dominate the remaining
input, so reducing evidence bytes cannot yield an equally large whole-prompt
reduction.

Cached-input counts vary from 0 to 9,216 despite identical within-case content,
and runner durations vary as well. They are retained but do not support latency
or cache-efficiency claims. Output length also varies with sampled wording.
Served model identity and monetary cost are unavailable.

## Validation correction

The measured `planner_evidence_v1.py` validates actual status, value, digest,
request identity and authority, but its call to the reply validator derived the
expected contract from the evidence itself. After the model experiment, review
found that an UNKNOWN record with its contract entirely omitted could pass that
narrow check. All four measured records contain valid explicit contracts, so the
bug did not alter their compact views or model inputs. The measured source and
all model records remain frozen.

`planner_evidence_v2.py` first runs the independent bounded contract validator,
then checks the reply against that validated contract. It additionally rejects
missing, malformed, unsupported and oversized contracts. On all four valid live
records, v2 output is JSON-byte-identical to the measured v1 output. Thus the
recorded model prompts are also the exact normal-case prompts produced by v2;
no post-hoc output substitution is needed. V1 is experiment evidence and should
not be promoted. V2 is the current candidate.

The first audit attempt also exposed platform-specific paths: the experiment was
run by Windows Python while the audit ran under WSL. A second attempt normalized
relative separators but not absolute image paths. Both failures, audit-source
hashes and their lack of effect on the already completed calls are retained as
`audit-failure-01.json` and `audit-failure-02.json`. The final audit normalizes
both and passes.

## What the compact view does and does not mean

The view is presentation over evidence that the durable caller has already
validated. It is not a validator for arbitrary wire input. It does not grant a
lease or input authority, authorize retries, close an observation window, prove
that a program caused an application effect, or replace independent final
scoring. UNKNOWN still requires interpretation of the current screenshot and a
fresh admission before new input. VERIFIED may finish only when a previously
declared completion policy accepts the exact evidence scope.

The fixed replay demonstrates preserved decisions in these four states and a
measured token reduction. It does not prove that every detail omitted from raw
history is irrelevant in unseen failures, nor does it measure live task speed.
Before making compact evidence the default, use v2 in a fresh live episode and
add adversarial cases where conflicting identities, partial programs, unavailable
verification and redacted observations genuinely change the next decision.

Follow-up: [the fresh live form episode](COMPACT_LIVE_FORM.md) passed with one
compact-driven model action. [Planner evidence binding](PLANNER_EVIDENCE_BINDING.md)
adds caller-expected request/contract checks and refuses nine adversarial controls
before model delivery. Its first partial-evidence model comparison is retained as
confounded and does not close the partial, unavailable or redacted decision gates.

Relevant artifacts:

- `results/planner-evidence-controls-01/`: measured-v1 valid and malformed
  evidence controls.
- `results/planner-evidence-controls-02/`: strict v2 contract controls and exact
  valid-output equivalence.
- `results/compact-evidence-decisions-01/`: plans, full/compact evidence, prompts,
  16 raw model calls, failures and final audit.

Issues #34 and #39 motivate retaining effect/UNKNOWN semantics. Issue #38 is
relevant to future redacted observations: omission by policy must be explicit
and must never become false absence. This experiment compresses validated
transport detail; it does not yet implement privacy redaction.
