# Issue #57 Chromium V5 → caller v3 → compiled GUI R03

## Prior setup stops

R01 and R02 are immutable setup STOPs, not task results. R01 stopped at the
module import; R02 stopped while hashing its not-yet-written conditions file.
R03 uses the absolute package import and writes `conditions.json` before
hashing it. It is a fresh, separately frozen allocation.

## Frozen question and limits

Can the exact V5 point-derived mint method and real `TargetHandleStore` use
pixels captured from a local Edge page to admit a two-action method through
adaptive caller v3 and compiled GUI, then refuse the second action after the
same target navigates to a new document generation?

- Base main: `3979669f5fb25115cd38ab67fba219ba3d87f494`.
- One positive and one changed-generation case, once normally and once with
  `python -O`. These are mode validations, not statistical repetitions. No
  retry within R03.
- Fresh headless Edge profile and loopback form. Fixture-fixed target points;
  no model/provider calls or external network.
- CDP mouse press/release and `insertText` only. No OS input, native focus,
  HWND identity, or physical release claim.
- Exact HTTP POST body is the independent task scorer.

## Pass criteria

Positive: both point mints have exact fresh patches and private registry IDs;
caller revalidation and both compiled admissions pass; Edge receives entry
then Submit; both CDP release receipts pass; the server records exactly one
exact POST; caller v3 returns `TASK_SUCCEEDED` with two completed transitions.

Changed-generation: the first action is retained and the page reload restores
the exact token; the document loader changes; the second admission is refused
as `SCOPE_MISMATCH/window_generation_changed_or_missing` before its execute
callback; caller v3 returns `EXECUTION_INCOMPLETE` with one completed action;
no POST or outer task-success verdict exists.

Save conditions, source hashes, every screenshot, raw runner output and exit,
receipts, release fields, post data, and cleanup outcome. Any missing evidence,
OCR mismatch, browser/setup failure, timeout, or cleanup error is a failure or
STOP. This experiment cannot establish provider economics, OS input release,
reliability, MAP01/Calc, or runtime distribution readiness.
