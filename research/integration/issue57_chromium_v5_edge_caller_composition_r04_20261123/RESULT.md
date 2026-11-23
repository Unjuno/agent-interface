# R04 result — FAIL_OCR_TOKEN_PUNCTUATION

## Disposition

**FAIL_OCR_TOKEN_PUNCTUATION; no task success.** In the normal-mode positive
case, the exact V5 point-mint method created both private aliases from actual
Edge screenshots, caller reuse and final revalidation passed, and the
compiled path admitted and dispatched the first CDP typing action. The next
observation visibly showed the exact `t991025-4`, but Windows OCR returned
`t991025` in the isolated input crop and `t991025 ・ 4` on the page. The
exact-token check did not match, so the compiled runtime returned
`effect_failed`/`EXECUTION_INCOMPLETE` after one completed action. Submit was
not called, the local server recorded no POST, and the outer scorer did not
run. The exactness gate remained intact.

The changed-generation case and `-O` run were not started after this first
case failed. This is not a successful composition, OCR qualification,
provider-efficiency result, or reliability estimate.

## Evidence

- Frozen protocol and source hashes: [`PROTOCOL.md`](PROTOCOL.md), [`raw/normal/conditions.json`](raw/normal/conditions.json).
- Runner output and exit 1: [`raw/normal.stdout.txt`](raw/normal.stdout.txt), [`raw/normal.exit.txt`](raw/normal.exit.txt).
- Actual screenshots, OCR observations, handle mint evidence and caller/core receipt: [`raw/normal/positive/`](raw/normal/positive/).
- The R04 cleanup helper initially left its test profile locked. Only Edge processes matching that generated R04 profile were stopped; a follow-up query found none and the profile was removed. See [`raw/cleanup-audit.json`](raw/cleanup-audit.json). The task verdict is unchanged.

## Interpretation and next boundary

Increasing fixture text size and isolating the input crop did not make Windows
OCR preserve the hyphen and following digit as one exact token. This is a
retained OCR limitation for this font/fixture condition. R05 may test an
alphanumeric task token under the same exact-match and independent-POST gates
to isolate punctuation segmentation. It must remain a separately frozen
condition and cannot turn R03/R04 into passes. Native OS input/release,
external providers, second-domain Calc, matched efficiency and public runtime
readiness remain untested here.
