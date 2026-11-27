# Issue #57 Chromium V5 → caller v3 → compiled GUI R06

## Frozen rationale

R05 reached the local form's exact POST effect, but the fixture's visual
completion predicate required OCR spaces that Windows OCR omitted
(`AIINTEGRATEDSAVED`). R06 normalizes non-alphanumeric separators for that
banner predicate only. Exact task-token OCR (`t9910254`), actual handle-store
validation, caller behavior, and the independent exact-POST scorer remain
unchanged. R05's failure packet remains immutable.

## Question and limits

Does separator-normalized completion-banner recognition let the composed
V5/caller/compiled path report success for the exact local task, while a real
same-target document-generation change still refuses the later action?

- Current-main base: `3979669f5fb25115cd38ab67fba219ba3d87f494`.
- Run positive and changed-generation cases once in normal Python and once
  under `python -O`. These four runs validate mode behavior; they are not
  independent reliability samples. Stop the sequence on the first failure.
- Use a fresh headless Edge profile and loopback-only HTTP form. Known fixture
  points, actual screenshots, Windows OCR, zero provider/model calls.
- Input uses Edge CDP only, not OS input or physical release observation.

## Pass criteria

Positive case: both handles mint from the exact fresh-patch method without
private IDs escaping; caller and compiled admissions pass; exact token OCR
passes; both actions complete; OCR sees the success banner under separator
normalization; the server receives exactly one exact `value=t9910254` POST;
independent scoring and caller return `TASK_SUCCEEDED`.

Changed-generation case: entry and exact token observation complete; a same-
target reload changes loader identity; the next real handle-store admission
refuses as `SCOPE_MISMATCH/window_generation_changed_or_missing` before its
execute callback; caller returns `EXECUTION_INCOMPLETE` with one completed
action and no POST or outer success score.

Retain every result and failure. No retry within an allocation. The result
cannot establish native input release, provider cost, repeated reliability,
Calc/MAP01, matched efficiency, or public-runtime readiness.
