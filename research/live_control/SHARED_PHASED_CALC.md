# Shared phases on actual Calc: correct artifact, costly interaction

shared_phased_calc_v1.py applies the unchanged shared phased caller to a second
desktop application. Actual screenshot/model decisions fill A1=480, A2=192,
save sheet.xlsx in Excel format, handle its visible confirmation dialog, and
request independent verification. There is no scripted editing or dialog
confirmation. The existing numeric schema is parsed directly from raw model
JSON. This experiment requires each act to begin with a click; it is not the
same prompt or action policy as the earlier Calc baselines.

The workbook is correct, but this is not evidence for promoting the policy:

1. Model clicks A1 and enters480 successfully.
2. Model proposes A2 entry and Save; sampled target patch changes, so no input
   is sent for this proposal.
3. A new model decision proposes A2 entry and Save. Activation succeeds, but
   the keyboard program returns needs_decision as the format dialog changes
   focus. Partial application effects remain visible.
4. Model clicks the visible Excel-format confirmation. The click also returns
   needs_decision as the dialog closes. No keyboard tail exists or is replayed.
5. Model clicks the sheet and issues another Save, which completes.
6. Model verifies both values and no remaining dialog. Independent workbook
   parsing confirms480/192.

The extra Save is a new model decision, not an automatic transport retry. The
patch refusal's visual cause has not been established; do not label it a cursor
blink or disable the freshness check without evidence. Likewise, interrupted
program status does not itself establish failed application behavior.

This one episode takes60.808s from initial capture to independent evaluation,
with six model calls,58,775 input tokens (20,992 cached) and1,214 output tokens.
Runner times are10.798/8.221/10.559/9.575/8.383/6.507s. Three sampled handoffs
take218.064/231.406/367.230ms. Audit replays174 events,28 exact frames,31 durable
exchanges, journal continuity, source and model provenance, pixel checks, and
the entire shared caller against the recorded responses. All input releases
are verified; two terminals are needs_decision and the rest completed.

The first audit incorrectly required byte-identical prompts across Linux and
Windows. LF/CRLF differed; decoded text agrees. The failure is retained in
audit-initial-failure.json, and the audit uses universal-newline UTF-8 text
comparison. No live rerun or experiment-code modification was used. Evidence
is results/shared-phased-calc-01; audit_shared_phased_calc_v1.py replays it.

Decision: keep phases opt-in. Mandatory initial clicks, exact patch refusal,
and program-level interruption feedback add decisions on this GUI workflow.
This supports studying whether sampled changes and completed UI transitions
can be presented more usefully to the model, rather than assuming more gates
improve end-to-end control. Next inspect the refused cell patch and the actual
post-dialog observation, then choose a bounded change that reduces unnecessary
decisions without hiding partial effects. A second desktop app is not broad
domain coverage; real-time games and human-like tempo remain separate open work.
