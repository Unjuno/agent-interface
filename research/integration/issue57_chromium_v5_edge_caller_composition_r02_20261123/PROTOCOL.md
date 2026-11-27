# Issue #57 Chromium V5 → caller v3 → compiled GUI R02

## Why R02 exists

R01 is retained as `STOP_SETUP_IMPORT`: its runner imported
`model_point_target_v1` before exposing the live-control module path, so no
Edge process or task case ran. R02 is a new source and evidence allocation with
an absolute package import. It does not reinterpret or replace the R01 result.

## Frozen question and conditions

Can the exact V5 point-derived mint method and real `TargetHandleStore` use
pixels captured from a local Edge page to admit a two-action method through
adaptive caller v3 and compiled GUI, then refuse its second action after the
same target navigates to a new document generation?

- Current-main base: `3979669f5fb25115cd38ab67fba219ba3d87f494`.
- One positive case and one changed-generation case in normal Python; the
  same two cases once under `python -O`. Modes are contract checks, not
  independent statistical repeats. No retries within R02.
- Fresh headless Edge profile, local loopback form, actual page screenshots and
  Windows OCR. Target points are fixed fixture coordinates; there are zero
  provider/model calls and no external network.
- Actions are sent through Edge CDP. The experiment does not exercise native
  Windows input, prove physical release, or produce efficiency data.
- The HTTP server independently scores exact POST content. The negative case
  reloads the page after typing, restores the value from local storage, and
  requires the handle store to refuse Submit on changed loader generation.

## Pass criteria

Positive: both point-derived aliases mint with exact source/fresh patch
equality, real store revalidation and both compiled admissions succeed, the
page receives entry and Submit, both CDP release receipts are retained, one
exact POST is independently scored, and caller v3 returns `TASK_SUCCEEDED`.

Changed-generation: first entry/release and visible exact value survive the
reload, the second admission returns `SCOPE_MISMATCH` with
`window_generation_changed_or_missing`, the execute callback is not called for
Submit, caller v3 returns `EXECUTION_INCOMPLETE` with one completed action,
and no POST or outer success score exists.

Record every stdout, exit, screenshot, condition, caller/core receipt, cleanup
result, and deviation. Any assertion, OCR, browser, timeout or cleanup failure
is retained and fails its case. Do not claim OS release, provider accounting,
reliability, MAP01/Calc coverage, or measured efficiency from this test.
