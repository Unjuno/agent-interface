# Issue #57 Chromium V5 → caller v3 → compiled GUI R05

## Frozen rationale

R03/R04 both stopped correctly after exact OCR failed on `t991025-4`; the
retained images show Windows OCR splitting or dropping the hyphen and suffix.
R05 tests punctuation-free token `t9910254` in the same larger, high-contrast
fixture introduced in R04. The exact-match acceptance rule and independent
POST scorer are unchanged. This isolates OCR punctuation segmentation; it is
not a comparison of the R03/R04 task token against a new task or a general OCR
qualification.

## Frozen question and limits

Can exact V5 point-derived handles from local Edge screenshots traverse caller
v3 and compiled GUI for a two-action exact-value form task, and does a real
same-target page reload make the second action refuse on changed document
generation?

- Current-main base: `3979669f5fb25115cd38ab67fba219ba3d87f494`.
- One positive and one changed-generation case in normal Python, then once
  with `python -O`. These are mode validations, not independent statistical
  repeats; no retries within R05.
- Fresh headless Edge profile, loopback-only HTTP form, fixed known-fixture
  target points, actual screenshots and Windows OCR; zero model/provider calls.
- CDP mouse/text dispatch only; no OS input or physical release evidence.
- Exact task value: `t9910254`. The independent scorer requires exactly one
  POST with that value.

## Pass criteria

Positive: both V5 aliases mint with exact fresh-patch matches and no private
registry ID exposure; caller revalidation and both compiled admissions pass;
OCR observes the exact token; both actions and CDP release receipts complete;
the server records one exact POST; independent scorer and caller return
`TASK_SUCCEEDED`.

Changed-generation: the first action completes and the exact token remains
visible after reload; loader identity changes; Submit admission refuses as
`SCOPE_MISMATCH/window_generation_changed_or_missing` before its execute
callback; caller returns `EXECUTION_INCOMPLETE` with one completed action and
no POST or outer success score.

Any missing predicate, wrong/duplicate POST, OCR ambiguity, browser failure,
timeout or cleanup failure is retained as FAIL/STOP. A failure in the first
case stops the allocation before the negative case or optimized run. This
cannot establish provider cost, OS input release, repeated reliability,
Calc/MAP01, or public runtime readiness.
