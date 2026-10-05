# Run record

- Experiment ID: `owner-nonneutral-release-a01`
- Executed: 2026-10-05 UTC on the Windows workstation; runtime versions pinned in `SOURCE_LOCK.json`.
- Frozen references: main `3f24e85bff32a93fbc1ca244f7f249b843710743`; #7847 parent `e00c7f5e5c949095d40ade458355e55ea5990b9d`; #7847 head `e412e2e70f69183512b88e54d69a483dfa8589e4`.
- Exact source Git blob IDs are in `SOURCE_LOCK.json`; `audit.py` recalculates both Git blob identities from retained bytes.

## Commands

The package's `run.ps1` runs these three invocations with `OWNER_SOURCE_PATH` set to each retained source:

1. `python -B test_non_neutral_release.py T.test_non_neutral_successful_aggregate_must_fail_closed` against `baseline_input_owner_v13.py` — expected RED, 1 failure.
2. `python -B test_non_neutral_release.py` against `published_input_owner_v13.py` — expected RED, 1 failure and 2 passing controls.
3. `python -B test_non_neutral_release.py` against `input_owner_v14_candidate.py` — GREEN, 3 tests passed.

`python -B audit.py` verifies source and test hashes, original Git blobs, exact one-hunk patch, regression and control outputs, and the complete file manifest. The audit does not participate in the test outcome.

## Environment and disposition

Python 3.11.9, PowerShell 7.6.5. Docker CLI is absent. Xlib, display creation, and injection are replaced by fake modules in the test; no native display or OS input was touched. This is a local construction result, not a formal/live allocation. All three outcomes and the initial harness assertion failures are retained separately.

The source change is only a research candidate stacked on #7847. No main-branch runtime integration, gameplay, application effect, useful feedback, bounded recovery, safety, or performance conclusion follows.