# Strict compact evidence in one live Chromium action

This study connects the strict `planner_evidence_v2` presentation to an actual
model decision. A fresh private Chromium fixture used seed 241. The caller lost
the connection after each saved-effect query, recovered the durable reply by
request ID, and did not resend either query. The first recovered result was
`UNKNOWN`; its 621-byte compact view and the current screenshot were delivered
to the model. The model proposed one form-field click/input program with value
`t000241` and Return. The program completed, the page displayed its confirmation,
and a second recovered query returned `VERIFIED`. Independent evaluation found
the exact saved value. No input was admitted after verification.

This is the first live integration check for the strict compact candidate. It
shows that the compact view can drive the intended action in this scoped case
while the full durable record remains available to the caller and auditor. It
does not establish a general reliability rate or a causal speed improvement.

| Quantity | Observed value |
| --- | ---: |
| Model calls | 1 |
| Model-visible evidence bytes | 621 |
| Input / output / reasoning tokens | 9,592 / 100 / 27 |
| Model runner | 6.542 s |
| Form-source capture to independent evaluation | 8.521 s |
| First runtime capture to independent evaluation | 9.706 s |
| Caller handoff | 230.173 ms |
| Saved-effect query losses / recovery reads / resends | 2 / 2 / 0 |
| Exact runtime frames / durable journal frames | 13 / 31 |

The earlier fixed-image comparison measured 621 bytes and 9,614 input tokens
for the same form-UNKNOWN evidence class, compared with 958 bytes and 9,727
tokens for the full view. The present live request reported 9,592 input tokens.
These runs differ in live screenshot, seed, prompt wording, cache state and model
sample, so their wall times and token totals are not a controlled pair. The
fixed comparison remains the evidence for the 113-token per-call reduction in
this evidence class; this episode establishes live wiring and task success.

The measured driver routes both the initial and any later UNKNOWN decision
through the same strict presenter. This episode reached VERIFIED after its first
action, so the later replan branch was not exercised. It therefore does not prove
compact presentation under multi-turn interruption. A successor study should
test conflicting identity, missing evidence, partial programs and unavailable
verification before default adoption.

Artifacts are under `results/compact-live-form-01/`. The independent audit checks
the measured source hashes, exact compact text, raw event and journal continuity,
all image reconstructions, query loss/recovery identity, absence of query resend,
program release, saved value, no post-verification input and owned-process cleanup.
Re-run it with:

```sh
python3 research/live_control/audit_compact_live_form_v1.py
```
