# C12 evidence rescue and audit correction

This additive successor preserves the original C12 package, including `RUN.json`, `AUDIT.json`, all six raw output/exit files, and the initial failed combined-process run. None of those predecessor files is rewritten.

## Review finding addressed

PR #7519 head `e5396957e8b7a3e7f2a42d9386a6d8575870f920` was reported mergeable with its replay gate passing. The repository-owner review on that exact head identified that `RUN.json` names the nonexistent `raw/candidate-exit.txt`, while the actual runner and `exit_receipts` list name `raw/composition-exit.txt` and `raw/publication-control-exit.txt`. The original `audit_c12.py` did not validate the singular field and consequently still emitted `PASS_COMPOSITION_SCOPED`.

`RUN_V2.json` is the explicit corrected receipt contract. `audit_c12_v2.py` requires the exact manifest shape, validates all six declared output/receipt paths, checks the three recorded exit values, and verifies the frozen `SOURCE_PINS.json` plus all 37 pinned source files. Its output is `AUDIT_V2.json`; the historical `AUDIT.json` remains untouched. Six mutation controls cover the valid package, bad path, bad exit value, missing member, unexpected legacy field, and changed frozen source.

## Verification on this rescue tree

- `python3 -B audit_c12_v2.py`: `PASS_COMPOSITION_SCOPED`, 37 source pins, all manifest/raw checks satisfied.
- `python3 -B -m unittest -v test_audit_c12_v2`: 6/6 PASS.
- In a disposable copy, `python3 -B audit_c12.py` reproduced the old auditor's PASS despite the stale singular receipt path. In a separate disposable copy, `python3 -B run_c12.py`, the V2 audit, and all six mutation controls passed.
- Regenerated unittest logs were not byte-identical to the archived raw logs: the originals use CRLF while the regenerated outputs use LF, and elapsed test durations vary. The archived bytes remain preserved; no byte-identity claim is made for these newly executed logs.
- `git diff --check` and the repository workspace-index check are expected to run against the final rescue commit before publication.

## OrbStack stop

The requested container attempt used the installed OrbStack Docker context, `python:3.12-slim`, `--network none`, and a read-only repository mount. It stopped before the container started because the daemon could not read the image blob (`operation not supported`). No container result is claimed. Native Python 3.14.5 was used as a transparent fallback; this is not equivalent to the pinned/container environment.

## Scope

The result remains host-side synthetic software-construction evidence. It establishes no live X11, physical key-up, game/application effect, recovery efficacy, performance, or Issue #59 completion. The original PR's three add/add production conflicts are not resolved by this evidence-only rescue.
