# V31 compressed typed soft-event context

V30 proved that a typed soft health transition can preserve an admitted
nonempty cover until the matching planner turn completes. It retained the event
locally, but the following planner turn received only the new temporal sheet,
current checked health, and no-visible-effect action names. V31 closes that
state-transfer gap without creating another observation or model boundary.

## Contract

Immediately before the already-required next planner turn, the controller reads
only the preceding decision's newest soft event. It validates that the record:

- is a `SOFT_CHANGED` health event inside the validity envelope;
- preserved existing policy and did not require a new decision;
- grants no input authority and may only preserve or reduce existing authority;
- has consistent sequence, signal, current value, hard floor, iteration, and
  cover-source fields.

Missing evidence becomes JSON `null`. Inconsistent or authority-granting
evidence raises an error instead of being summarized. The summary contains only
signal, source/current/floor values, count, sequence, interval/source iterations,
the already-recorded preservation effect, and `grants_input_authority:false`.
It excludes timestamps, glyph scores, WAD hash, binding geometry, and duplicated
guard prose.

For retained v30 decision 4, the full event is 1,312 compact-JSON UTF-8 bytes and
the v31 summary is 240 bytes. This is a byte-size construction measurement, not
endpoint token savings. The summary is added to the same prompt and same image
that the following turn already requires, so it adds zero image captures, model
calls, planner resumptions, or mid-turn boundaries.

## Model-free verification

Nine controller tests pass on Windows and WSL/Linux. They preserve all v30
schema, replay, hard interruption, verified release, and prompt-health tests,
and add retained-live checks for the exact `84→78`, floor74, count1, sequence73
summary. No-evidence returns null; inconsistent count/event state and a forged
input-authority grant fail closed.

No v31 live allocation has run. The next useful experiment should not repeat the
same fixed fixture merely to reproduce the v30 pass. First choose a different
reproducible threat state or a bounded normal-MAP01 continuation, freeze exact
transfer criteria, and measure whether the next planner response uses the typed
history correctly. A later full clear attempt remains a dynamic system test,
not the sole architecture benchmark.
