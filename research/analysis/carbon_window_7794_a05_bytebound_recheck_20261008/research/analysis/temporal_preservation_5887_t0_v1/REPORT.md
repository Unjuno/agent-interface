# Issue #5887 pre-run STOP recovery — not a scientific result

This is a preservation-only integration of the frozen T0 preregistration, candidate, and corrected independent auditor. No experimental entrypoint was run during recovery.

## Allocation state preserved from the owner Issue

- Allocation: `TEMPORAL-PRESERVATION-5887-T0-20261001-01`.
- Original source branch tip: `ce3ec73c4803c3537ad6332bc13f932b6aa2ae73` (`research/5887-temporal-preservation-t0-20261001`).
- Initial launch-gate STOP: `STOP_MAIN_ADVANCE_AND_STORAGE_BELOW_MINIMUM`; candidate/auditor/container = 0/0/0; scientific outcome `NOT_EVALUATED`.
- The planning main had advanced after freeze, and available C: storage was 54,030,336 bytes against the preregistered 64 MiB minimum. The pinned image checks did not override these failed gates.
- Later read-only continuation recheck recorded storage exhausted at 0 bytes and Docker CLI/inventory unresponsive. No successor invocation, retry, rebase, candidate, auditor, or container run occurred. The Docker service start attempt was permission-gated and did not change service state.
- The owner Issue says to resume only under a distinct fresh allocation after storage, Docker responsiveness, current-main refreeze, and collision/resource checks are satisfied. This PR performs none of those actions.

## Preservation checks and scientific boundary

- Original `PREREGISTRATION.md`, `candidate.py`, and `audit.py` are retained byte-for-byte from the source tip.
- Local validation parses both Python files with `ast`; it does not import or execute candidate/auditor code.
- This package contains no raw result and supports no PASS, FAIL, or HOLD on the frozen temporal hypothesis. The source remains a prepared but unexecuted finite synthetic method test.
- No human, live GUI, model, production scheduler, or real-world temporal preservation behavior was tested.

Issue #5887 remains open. Prior STOP records are not rewritten or treated as reusable allocations.
