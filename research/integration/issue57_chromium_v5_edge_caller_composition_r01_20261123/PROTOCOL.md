# Issue #57 Chromium V5 → caller v3 → compiled GUI R01

## Frozen question

Can the exact V5 point-derived mint method and real `TargetHandleStore` use
pixel evidence captured from a local Edge page to admit a two-action method
through adaptive caller v3 and compiled GUI, and refuse its second action when
the same page target has navigated to a new document generation?

## Scope and exclusions

- Base: current main `3979669f5fb25115cd38ab67fba219ba3d87f494`.
- Domain: isolated, headless Microsoft Edge and a private loopback HTML form.
- Target points are fixed by the known test fixture. There are no model or
provider calls, no external network access, and no claims about model cost.
- Browser actions use Chrome DevTools Protocol (CDP): mouse press/release and
`Input.insertText`. This does not exercise Win32/X11 physical input or prove
physical input release.
- The synthetic `pointer_binding` identifies the Edge page target, loopback
surface and document loader generation. It is not an HWND or OS focus receipt.
- The HTTP server independently scores the exact submitted form value.
- This is one positive and one invalidation case in each Python mode. Normal
and optimized runs are validation modes, not independent statistical repeats.

## Procedure

1. Launch a fresh Edge profile and a local form with an empty field.
2. Capture the actual rendered page and call the exact V5
`session_v33.Backend.execute` point-mint method for the field and Submit
controls. Retain exact patch hashes and private-registry-backed aliases.
3. Use the real handle store to revalidate both aliases before execution.
4. Run caller v3 with its actual compiled-GUI executor. The method types the
known task token, observes it with Windows OCR, then selects Submit from that
intermediate observation.
5. Independently inspect the local HTTP POST body and retain action/release,
caller, compiled receipt, OCR, screenshots, browser identity, and cleanup.
6. Repeat once with a real page reload after typing. The fixture restores the
typed token from local storage; the document loader generation changes. The
compiled path must refuse Submit at admission, retain the completed first
action, and produce no task-success score or HTTP POST.
7. Execute both cases in normal Python and once under `python -O`. Do not retry
failed cases within this allocation. Preserve setup, assertion, timeout, and
cleanup failures in place.

## Frozen acceptance criteria

Positive case passes only if both V5 handles mint with exact fresh-patch
matches, both caller revalidations and both compiled admissions succeed, the
actual Edge page receives the two operations, both CDP release receipts are
retained, the server records exactly one exact POST, the independent scorer
returns success, and caller v3 returns `TASK_SUCCEEDED`.

Changed-generation case passes only if the first typed operation and its
release are retained, the reloaded page visibly restores the exact token, the
Submit handle is refused with `window_generation_changed_or_missing` before
its execute callback, caller v3 returns `EXECUTION_INCOMPLETE` with one
completed action, and no POST or outer task-success verdict exists.

Any missing evidence, model call, non-loopback request, failed cleanup, hidden
retry, missing generation change, or mismatch between the visible token and
server body is a failure or scope deviation; it cannot be reclassified as a
pass. These results cannot establish provider accounting, OS input release,
MAP01/Calc coverage, repeated reliability, or an efficiency improvement.
