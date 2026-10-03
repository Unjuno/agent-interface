# Independent current-main integration review

This is a rescue of abandoned PR #6866, original head
`abd318643112150d073a242926494145c6461e33`, onto current main
`bb6bceb7c089112a9fe52c43a48310bf0b96bfac`. It is ordinary engineering
verification, not a formal scientific allocation or native-backend qualification.

## Preservation and combination

All 40 original evidence-package files remain byte-identical to the original
head, and their 39 declared checksums match. The original regression test is
also unchanged. The original README describes the old proposed-delivery state;
this additive review does not rewrite that history or recover its lost private
logs.

Current main's contract has advanced since the original review base. Only the
three intended `_bounded_int` calls are applied; the older entire contract is
NOT restored. Current-main original contract SHA-256:
`88122eab96fe907dcdaac032e8d9c82555d5d1adfe7bf8a9741274f19347d8a9`.
Combined repaired contract SHA-256:
`1709078c2a144d78ab61a9bc59fbb9973c120b9a58101c079d69db65d43a66b1`.
Existing exact-expiry equality and valid freshness/refusal ordering are retained.

## New local evidence (macOS, CPython 3.14.5)

The new raw logs are separately retained in `current_main_combination/`, with
their own manifest. Nothing replaces the earlier Windows checks.

- RED on current main with the original eight regression tests: exit 1,
  44 failures and four type exceptions.
- GREEN after the three-call patch: all 87 core tests pass, exit 0.
- Applicable portable CLI/review/static validation/distribution/native-probe
  and pure Quartz checks: 165 tests, exit 0, six explicitly skipped cases.
  Real Quartz/native input integration was NOT invoked.
- Production Win32/X11/Quartz session code with native imports replaced by
  recording backends: 21 rows; 18 structured refusals without preflight,
  execute or release calls, and three valid controls with one logical spy call.
- Separate raw-only audit: `PASS_SESSION_ADMISSION_CHECK`, zero errors;
  omission, duplication, fabricated NaN admission, hidden execution and boolean
  counter mutations are rejected. Native backend source is not changed.
- Core compilation passes. Side-effect-free doctor reports native backend not
  loaded, no input authority, and no readiness for side effects.

The first checksum-check invocation resolved package-local `.gitattributes`
against the repository root and failed. Correct package-relative resolution
then verified all 39 entries; no original evidence was changed to make it pass.

## Container limitation and decision boundary

Container-first availability was inspected on Docker context `orbstack`.
Image inventory failed with a containerd blob read error (`operation not
supported`, blob `65c2693c72adad38c529f1483e7b315defce13c59eb02bcd459285716379c826`).
No image was pulled, no container was launched, no shared runtime was repaired
or reset. Container validation is STOP_RUNTIME_UNAVAILABLE, not PASS.

**H:** malformed current evidence must be refused before freshness/capability
comparison while valid behavior remains unchanged. **T:** red/green core tests,
portable downstream checks and recording-backend session audit on current main.
**D:** PASS_LOCAL_ENGINEERING_COMBINATION for the exercised gates only.
**C:** public dispatch already checks some values; this is the direct-call
boundary, not a demonstrated GUI exploit. **U:** physical input, clock-domain
consistency, timing, real host-backend behavior and cross-platform CI are not
established by these local checks. No committee vote or two-reviewer approval
is fabricated; original draft-review state remains historical evidence.

The user authorized recovery/integration of abandoned branches and local-first
CI. Integration still uses a normal PR and GitHub merge API under branch rules.
