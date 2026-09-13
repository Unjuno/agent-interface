# Actual pixel redaction and explicit unknown semantics

This study tests a narrow part of Issue #38: whether a current live GUI region can
be physically withheld from the model while the planner receives an explicit
`REDACTED_BY_POLICY` state instead of treating missing evidence as absence.

## Fixed comparison

A fresh private Chromium fixture, seed 250, displayed `t000250` in the Value
field. The harness retained one exact source observation and created two model
inputs from it:

- **full:** the unchanged source PNG and a full-view record;
- **redacted:** the field pixels replaced by a source-independent pattern and a
  typed record declaring the content unknown, raw history unavailable, and no
  authority to target, transcribe, verify, or infer the region.

The fixed ABBA-style order contained four Luna/low calls per condition. The full
condition read `t000250` exactly in 4/4 calls. The redacted condition returned
`UNKNOWN / REDACTED_BY_POLICY` in 4/4 calls and never emitted the token. No GUI
action was allowed after presentation. Independent task success is intentionally
false because the study requested no submit or save action.

The v2 region contract declares
`LEFT_TOP_INCLUSIVE_RIGHT_BOTTOM_EXCLUSIVE`. The declared box
`[60,264,248,291]` exactly equals the bounding box of changed pixels. Two
synthetic source images that differ only inside a hidden region produce identical
presented pixels and bytes on the same encoder. Ten invalid policy cases and four
invalid response cases refuse without a model call or GUI action.

## Cost and limits

Across 100 renders of the selected live frame, local presentation cost was
38.757 ms median and 46.917 ms p95. The PNG changed from 41,630 to 40,289 bytes,
but model-reported input increased from 9,302 to 9,414 tokens per call because
the explicit policy record adds semantics. This is privacy-boundary and unknown-
state evidence, not token compression.

PNG compression bytes differed when the same pixels were encoded by the Windows
and Linux Pillow environments, while decoded pixels matched exactly. The audit
therefore requires cross-platform pixel equality and does not claim portable PNG
byte identity.

This does not yet test a task that must act around a redacted region, authorized
refinement, crop/history/alternate-channel bypass, OCR leakage, multiple regions,
adversarial inference, or a `presented_only` retention deployment. The retained
raw source is local under the declared `raw_local_only` study policy. These are
required before a broad privacy or production claim.

## Preserved failures

Revision 1 used Pillow's inclusive rectangle directly while its metadata did not
declare edge semantics. The declared box ended at `(248,291)`, but changed pixels
extended through those coordinates and produced an exclusive difference bound of
`(60,264,249,292)`. Revision 1 remains rejected even though its 4/4 full and 4/4
redacted model decisions were correct.

The first v2 cost invocation assumed the source was `runtime/009.png`; exact-frame
reuse bound the selected observation to `runtime/008.png`. That failed attempt is
retained in `results/redaction-cost-02`. The corrected measurement resolves the
source filename through the private audit binding.

Primary results:

- `results/redacted-observation-02/audit.json`
- `results/redacted-observation-controls-02/`
- `results/redaction-cost-03/`
- rejected `results/redacted-observation-01/audit.json`

Reproduce the final controls and audits from this directory:

```sh
python3 probe_redacted_observation_v2.py
python3 run_redacted_observation_v2.py
python3 measure_redaction_cost_v2.py
python3 audit_redacted_observation_v2.py
```
