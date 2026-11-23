# Issue #57 Chromium V5 → caller v3 → compiled GUI R07

## Frozen rationale

R05 demonstrated that OCR returned the completion banner as
`AIINTEGRATEDSAVED` while the fixture predicate expected spaces. R06 froze a
separator-normalization correction but stopped before tests because its
evidence directory was nested too deeply for the runner's protocol lookup;
zero tests ran and Edge did not launch. R07 evaluates the same correction
under a fresh run, with evidence root set exactly to `raw/normal` so the
frozen runner resolves this packet's `PROTOCOL.md`.

The exact task-token OCR, actual handle-store validation, caller behavior, and
independent exact-POST scorer remain unchanged. R05 and R06 records remain
immutable.

## Question and limits

Does separator-normalized completion-banner recognition let the composed
V5/caller/compiled path report success for the exact local task, while a real
same-target document-generation change still refuses the later action?

- Current-main base: `3979669f5fb25115cd38ab67fba219ba3d87f494`.
- Run positive and changed-generation cases once in normal Python and once
  under `python -O`. These four runs validate mode behavior; they are not
  independent reliability samples. Stop on the first failure.
- Use fresh headless Edge profiles and a loopback-only HTTP form, actual
  screenshots, Windows OCR, known fixture points, and zero provider calls.
- Input uses Edge CDP, not OS input or physical release observation.

## Pass criteria

Positive: V5 aliases mint without private IDs escaping; caller and compiled
admissions pass; exact `t9910254` OCR passes; both actions complete; the OCR
banner passes after separator normalization; the server records exactly one
`value=t9910254` POST; independent scoring and caller return `TASK_SUCCEEDED`.

Changed-generation: entry and exact token observation complete; same-target
reload changes loader identity; the next real handle-store admission refuses
as `SCOPE_MISMATCH/window_generation_changed_or_missing` before execute;
caller returns `EXECUTION_INCOMPLETE` with one completed action and no POST or
outer success score.

Retain every outcome. No retry within this run. This cannot establish native
input release, provider cost, repeated reliability, Calc/MAP01, matched
efficiency, or public-runtime readiness.
