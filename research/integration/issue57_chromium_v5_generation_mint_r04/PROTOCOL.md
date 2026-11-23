# Chromium V5 point-mint generation guard R04

R01/R02 stopped before target execution due to missing sibling imports. The
R03 environment preflight showed that importing V5's entire historical parent
chain requires unrelated openpyxl/Calc modules. R04 isolates only that unused
parent class while importing the exact `session_v33.Backend.execute` method.
No implementation source is changed for the baseline run.

## Frozen question

Does `session_v33.Backend.execute` refuse a point-derived handle mint when the
fresh observation has a different process or window generation from the
model's source observation, despite the exact pixel patch, focus, surface and
geometry being identical?

## Frozen schedule and acceptance

One normal and one `-O` run each execute three cases: process-generation-only
change, window-generation-only change, and unchanged-generation positive
control. Both negatives must raise the typed pre-input `DecisionRequired`, emit
`handle_created=false`, and leave the real registry empty. The positive must
mint one session alias backed by the private store, with exact source/fresh
patch digest equality. No X server, browser, real input, external model or
provider is used. No retry or case replacement is allowed.

The R01/R02 setup stops and R03 import preflight are excluded from product
results and linked in `RESULT.md`; no attempt is silently pooled.
