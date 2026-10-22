# Run record — A07 STOP

- Allocation: `V39-V15-RELEASE-IDENTITY-A07-20261005-01`.
- Freeze/base: `FREEZE.json`, main SHA `aeed696ff756d68497faed39b92e3546cb144972`.
- Input: retained A02 raw SHA-256 `0336cfa2eeebbe48ad816168d5466938a936fcf0782211b21847df6c20038596`.
- Construction TDD before freeze: 5 tests passed. The test matrix included 14 identity mutations and a duplicate-release control; this is construction validation only.

The frozen A07 audit command was invoked once. `formal/AUDIT.json` and `formal/AUDIT.stdout` report a two-case baseline PASS and zero errors. The command's terminal output recorded `EXIT_CODE=0`, while the saved `formal/AUDIT.exit` contains `1`. This exit-status conflict is retained and not reconciled by rerunning.

The frozen independent-reference command was invoked once. It exited with saved value `0`, but `formal/INDEPENDENT_AUDIT.stdout` and `.stderr` are empty and the declared `formal/INDEPENDENT_AUDIT.json` was not created. Read-only inspection of the frozen `reference_audit.py` shows it defines the reference function but no CLI entry point, so the declared command could not generate the expected result.

**Disposition: `STOP_AUDIT_RESULT_PROVENANCE_INCONSISTENT`.** The independent confirmation gate did not produce a result and the candidate exit record conflicts with the observed terminal line. Do not promote the construction mutation tests or A07 baseline JSON to a formal method PASS. No retries, candidate/runtime invocations, code edits, or source changes occurred after freeze. The original A02 `FAIL` and all A03/A06 records remain unchanged.

Environment: Windows host, CPython 3.11.9, host-only pure-JSON processing; no claim of container isolation or resource enforcement. No WSLc, network, GPU, model, GUI, game, or input was used.
