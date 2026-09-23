# Common-runtime readiness: four applications

`results/readiness-01` is a scripted smoke cohort, not an actual assistant
performance study or a qualifying freeze revision. It addresses the shared
evaluation plan's uncertainty: can the same pinned runtime carry ordinary tasks
and reject an already-expired request across the currently selectable apps?

Before launching applications, `readiness_probe.py` wrote eight cases and all
reference runtime hashes to the manifest. The source hashes match the candidate
published at `7427bdd`: `interactive_v10.py`, full presentation, with the same
transitive owner, lease, focus, recovery and quiet-observation implementations.
The candidate was not modified during the cohort. The harness uses the client
and runtime's shared WSL monotonic clock for ten-second intent validity.

| Application | Ordinary case | Expired-request + task case | Saved outcome |
|---|---|---|---|
| XTerm | Pass | Pass | Exact task token |
| Chromium | Pass | Pass | Form submission contains exact task token |
| Calc | Pass | Pass | A1/A2 equal declared values, saved in workbook |
| Inkscape | Pass | Pass | Rectangle x=52, y=50, size 40×30, no transform |

Seeds 970101/970102 and the case order were fixed in the manifest. Inkscape uses
F1, Ctrl+A, Right and save: this verifies keyboard nudging, not dragging, pointer
input or general motor control. The oracle requires movement right while
preserving size/y, not the older harness's exact drag distance. App action
adapters are explicitly different; the runtime semantics and source are shared.

All eight tasks passed saved-artifact checks after control. Four expired requests
were rejected before acceptance or input admission. All twelve accepted task
programs completed with verified release; all eight owner shutdowns verified
release. Seventy-eight frames reconstruct from packets and match PNG pixels.
The auditor reopens saved text, form data, workbooks and SVGs and verifies source
hashes and full-output logs. Ordinary-case `stale_rejection_verified=false` in
the probe summary means not exercised; the audit represents this as null.

This is narrow readiness evidence. No new failure occurrence was observed in
these declared cases, but the global new-class count remains unknown because
historical discovery ordering is not audited. There is no new architecture
mechanism or promotion candidate in this work. Do not append these scripted
results to the historical self-use success curve without labelling a new cohort.

## Limits and next decision

The cohort does not cover active cancellation, expiry during held input, wrong
target delivery, transport loss, critical-event retention or live model delays
as shared cross-domain stress scenarios. Earlier focused tests remain separate
evidence. Continuous tracking and DOOM still need adapters to the same reference
semantics. This cohort does not qualify for the rolling freeze window.

Application versions were recorded **after** the cohort in `environment-after.json`;
they are retrospective environment documentation, not a preregistered environment
freeze. Source/case manifests were written before running. Next cohorts should
record environment versions before execution too. The scripts retain the research
runtime's process/connection timeout limitations; output is local full JSON.

The next highest-value readiness work is a declared shared stress manifest and
an inventory of tracking/DOOM adapter differences. Adding unrelated interaction
primitives remains deferred. Historical first-discovery backfill also remains open.

## Reproduce

In the documented Ubuntu/WSL environment from the repository root:

```sh
python3 research/evolution/readiness_probe.py --out results-local/readiness-new
python3 research/evolution/audit_readiness.py research/evolution/results/readiness-01
```

Choose a fresh output path. The original harness and result bytes are retained
through `.gitattributes`; source changes require a new measured revision.
