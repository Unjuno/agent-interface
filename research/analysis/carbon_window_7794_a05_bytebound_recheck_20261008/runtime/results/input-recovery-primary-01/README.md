# Primary use of explicit input recovery

On 2026-09-28 the primary assistant operated a fresh private Linux/X11 counter
window through the persistent public MCP runtime and instrumented Node relay.
The visible task was to save Count 2: W adds one; S saves the displayed count.
No helper model selected actions. Decisions were made after presenting the
retained replies and screenshots to the primary assistant.

The source-known fixture deliberately injected one acknowledgement exception
after the X server processed the first W press, then omitted the first cleanup's
release request. Thus the first operation returned execution_failed with W still
down. This is a constructed failure, not a natural incident or fault-rate study.
Autorepeat was disabled on this private X server; this matters to the outcome.

The assistant explicitly called interface_recover_input on revision 1. It
received verified empty release and revision 2, then observed the application.
The screenshot showed Count 1: the failed operation had already affected the app.
After reviewing it, the assistant authored one new W pulse and saw Count 2,
then sent S once and saw Saved Count 2. The failed program was not automatically
replayed. After closing the MCP connection, independent file readback found
saved count 2 and application events W/count1, W/count2, S/count2.

Seven MCP calls were retained: initial observation, failed input, explicit
recovery, post-recovery observation, remaining increment plus observation,
save plus observation, and close. Six primary review notes bind to exact reply
hashes. Initial and subsequent observation sequence numbers are caller assertions,
not server-issued freshness. Admission leases used prior relay return +120s;
they are not a hard execution watchdog. Successful new pulses used a 20ms hold
and explicit 100ms pre-capture wait; this does not adopt a pacing default.

The public runtime archive is retained in raw.tar.gz with SHA-256
`c44402dbce3454d701c978f3ea1d9cc345cff83c1463e0825c6b43e10018e78a`, built from
`c26f30a7b63766cc1aed1b0aa4b307ee3e4540c5`. Integration main at the trial was
`dbfae29cf848e4beee8f0287a9843532f5a695a8`; the exercised implementation is the
already integrated recovery code, with a local fault-injection wrapper.
Fixture/app/relay/fault sources, build metadata, request/reply journals, images,
host event timestamps, saved output, app events and cleanup are retained.

The session closed with verified release and the relay exited 0. Fixture cleanup
reaped Xvfb/Openbox/app with codes 0/1/-15 respectively; the app was terminated
by fixture cleanup after the saved task was reviewed, not a normal app exit.
The verifier checks retained bytes, call identity/order, session/revision,
failure/recovery receipts, review bindings, exact saved effects and process exits.
It does not independently interpret screenshot pixels or prove human reasoning.

Scope: one source-known, simple primary-operated construction supports usability
of explicit recovery followed by visual review and deliberate continuation.
It does not establish ordinary desktop task reliability, exact physical key
edges, first useful-feedback onset, matched recovery-cost reduction, actual
model tokens/cost, real-time benchmark performance or human-level tempo.
The prior programmatic controls remain in ../explicit-input-recovery-01.

Run `python3 -O runtime/results/input-recovery-primary-01/verify.py`.
