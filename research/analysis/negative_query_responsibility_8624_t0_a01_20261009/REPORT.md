# Issue #8624 T0 A01 result

**Disposition:** STOP_CANDIDATE_EXIT_AFTER_OUTPUT.

The frozen candidate was invoked once with python3 -B candidate.py model.json FREEZE.json on CPython 3.14.5 / macOS 27.0.1 arm64. It emitted a syntactically valid JSON file with seven case rows and CANDIDATE_COMPLETE, but then exited 1 because main() returned using the deleted local name errors:

NameError: name 'errors' is not defined

This is a candidate CLI execution STOP, not an audited method result. The candidate output SHA-256 is 70da66bafbc86f094591517ecb9af8c90b56534d915ce9b5ccafe644ee6d641b; stderr SHA-256 is b51e29257ce68836a16edbcca1a5cd10404384198dec378f3687b0a1c2defa2f. Both exact files are retained under results/.

The frozen gate required candidate exit 0 before the auditor could run. The raw file was nonempty but the process exit was 1, so auditor invocations are 0. No candidate retry, manual result adjudication, PASS/FAIL claim, or A01 relabeling is permitted. Any correction is a distinct successor allocation with new source identity, freeze, output path, and one candidate/auditor pair.

No live GUI, screenshot, model, user data, external effect, or action dispatch is part of this T0.
