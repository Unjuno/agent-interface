# Typed phase outcomes: classification improves, planner benefit not shown

The phased caller labels both a pre-input patch refusal and admitted interrupted
input as refused. Its raw terminal and event records already preserve the
distinction. This experiment derives a typed presentation from those records and
tests whether providing it to the model reduces unnecessary Save proposals.

## Adapter and controls

phased_outcome_v3.py is the current optional presentation helper. It retains the
v2 output format. It distinguishes not_submitted, admission_rejected,
protocol_pending, program_interrupted, programs_completed,
partial_sequence_stopped and evidence_unresolved. It matches each input program
by action ID, reports observed step starts/input ACK counts/terminal progress,
and blocks its input recommendation for unresolved delivery, closed channels or
unverified release. Passive observation release failures also block the view.

Program completion and input ACKs never imply an application effect. Effect
status remains unknown. The adapter performs no transport, cannot authorize
retries and preserves the original raw resolution in feedback. It expects
validated durable/phased results; it is not an untrusted wire validator or a
replacement for runtime admission. Numeric GUI proposal restrictions remain.

Twelve controls cover actual patch refusal, interrupted Save/confirmation,
completed input, real inter-phase focus refusal, synthetic pending delivery,
unrelated historical terminals, closed channels, unverified input/passive release,
missing admission evidence and unknown terminal status. Feedback copying and raw
resolution preservation are checked. The zero-completed-step confirmation still
reports two input ACK events; application effect stays unknown.

Earlier revisions remain available. V1's fallback could label missing admission
evidence as rejection, and its manifest used colliding turns.json basenames.
V2 corrects these and was used in the model comparison. V3 additionally handles
passive release failure; its views are byte-equivalent after JSON encoding to V2
for the three recorded comparison cases, as checked before publication. No model
comparison was rerun to select a better outcome after this repair.

## Fixed-case comparison

probe_outcome_decisions_v1.py predeclares12 read-only model calls using the same
image and common prompt prefix within each case. A retains the original feedback.
B replaces the aggregate phase label and adds the typed outcome while preserving
all other feedback, including the full terminal. No saved-workbook audit evidence
is supplied to either condition. Actual requested configuration is the existing
gpt-5.6-luna/low responder runner, with two calls per condition per case.

The post-confirmation and pre-input cases use ABBA order; the visible-dialog case
uses BAAB. The common replay prefix is present in both conditions, so these calls
are not replicas of the prior live model invocations. All outputs are proposals;
no GUI input or final verification was executed during this comparison.

| Fixed case | A decisions | B decisions | A input tokens/call | B input tokens/call | Mean runner seconds A/B |
| --- | --- | --- | ---: | ---: | --- |
| After confirmation, required values already persisted |2 verification requests|1 verification request,1 additional Save|10,064|10,274|6.745 /8.036|
| Format confirmation visible |2 clicks on Excel-format confirmation|2 clicks on Excel-format confirmation|10,114|10,410|9.437 /6.890|
| Prior A2 proposal refused before input |2 A2 entry/Save proposals|2 A2 entry/Save proposals|9,652|9,777|7.952 /8.004|

The control cases make no premature goal-verification request. Their decisions
are equivalent at the task level. In the primary case, B does not reduce
unnecessary Save proposals and adds125–296 input tokens per call across cases.
There are only two observations per condition. Cache usage differs and served
model identity/cost are unavailable; neither population reliability nor latency
effects can be inferred. Full usage and timing records remain in the audit.

## Decision

Do not adopt the expanded typed view as default model feedback. Correctly naming
program states did not demonstrate better planner decisions in these fixed
cases. The helper remains an optional programmatic diagnostic; the live runtime,
caller and default model presentation are unchanged. This is negative evidence
against this particular expanded presentation, not against maintaining precise
delivery/semantic-effect distinctions internally.

The next useful path is to evaluate explicit effect verification through existing
capabilities, rather than add more status text. The repository already has
saved_effect.py, optional non-final checkpoints (runtime29/socket14), archived
checkpoints and prepared_checkpoint_v2. The latest cause-servo/durable path does
not expose that same integration. Inspect and reuse those contracts before
creating another verifier; a checkpoint should remain scoped to a caller-declared
artifact contract and preserve UNKNOWN. A saved-file capability is not a universal
pixel-only GUI claim.

This narrows the next work on [Issue39](https://github.com/Unjuno/agent-interface/issues/39)
and [Issue34](https://github.com/Unjuno/agent-interface/issues/34). Their broader
promotion criteria, domain coverage and human-like live tempo remain open. No
GitHub issue comments or status changes were made.

Evidence: results/phased-outcome-controls-01 through03 and
results/outcome-decisions-01. audit_outcome_decisions_v1.py verifies all12 model
calls, exact image/prompt/source provenance, event arrivals, output parsing and
decision classifications. The original and repaired control sources/results are
retained, including their documented limitations.
