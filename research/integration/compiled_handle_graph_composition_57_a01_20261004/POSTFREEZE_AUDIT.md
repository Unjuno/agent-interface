# Post-freeze audit and execution custody

The candidate was run once from the frozen source/input bytes. Its complete JSON output is `out/candidate.json`. The first read-only audit is preserved at `out/audit.json` with its v1 implementation. A subsequent corruption probe found that v1 did not reject a top-level row summary that disagreed with its nested runtime receipt. V1 still derived counts from the receipts, but the inconsistency check was missing.

`audit_v2.py` adds that check without changing or rerunning the candidate. `out/audit_v2.json` passes the same 15 records. Three read-only corruption controls passed: (1) inconsistent row summary rejected, (2) field-race receipt claiming a transition rejected, and (3) submit-race operation list containing `activate_submit` rejected. The v1 auditor and result remain unchanged.

The first checksum command was invoked from the repository root even though `SHA256SUMS` contains package-relative paths; it printed unreadable-path errors. The shell continued to the candidate command because the lines were not joined with fail-fast control. Afterward, running the same checksum check from this package directory verified all 12 frozen source and input entries. The package bytes match `FREEZE.json`, but this does not retroactively make the checksum check a pre-run gate. Candidate process exit code and exact start/end timestamps were not captured. No candidate rerun was made.

A later consistency script initially required the frozen file set to equal the entire package, including additive post-freeze audit files; that script exited 1 on the expected extra files. Its corrected check verifies every frozen digest and requires `SHA256SUMS` to contain exactly the frozen entries. That check passed; no frozen file was changed.

One subsequent digest-check script also used repository-prefixed paths after changing its working directory into the package and exited when it could not open `FREEZE.json`; both checksum manifests had already passed. Re-running that check from the repository root passed.

The candidate JSON's `source_main` is `41df296f3ce4d03c801c998d38f6e537e64a83ab`, but `FREEZE.json` pins integration base `9dc383a89043deb6199c847196498d867ba6bb75`. The frozen gate says any mismatch is FAIL. The first read-only audit v3 attempt failed because its repository-root calculation selected the enclosing `work` directory; its empty stdout file is retained at `out/audit_v3.json`, and `RUNS.json` retains the observed failure. The corrected audit v4 sets the overall disposition to `FAIL_SOURCE_BASE_LABEL_MISMATCH`, while recording that all four runtime/handle module blob IDs at both commits match the frozen source IDs and the v2 behavioral audit meets its scenario counts. This module identity check narrows the discrepancy to the raw base label; it does not change the frozen failure or rewrite the candidate. No experiment was rerun.

The earlier `docker ps` probe was reported to fail because the OrbStack daemon could not read content blob `sha256:c1f24dda54ba0d4f3cabe7900b203ea25766c2403dc752895a8e54e3f6167cb8` (`operation not supported`). Its raw terminal transcript was not retained in this package. This study therefore ran natively on macOS, not in a container.

## Result

The retained candidate and v2 audit report behavioral counts meeting the scenario thresholds, but audit v3 assigns the frozen overall disposition `FAIL_SOURCE_BASE_LABEL_MISMATCH`:

- 5/5 stable-pixel cases reached test-double `TASK_SUCCEEDED` after exactly `enter_exact_token`, then `activate_submit`.
- 5/5 field patches changed between observation and admission and were refused as `missing_symbol` with zero executions.
- 5/5 submit patches changed between observation and the second admission and were refused as `missing_symbol` after the entry operation, with no submit operation.
- Every test-double execution reported a verified release with empty key and button sets.

These are adapter-composition and pixel-invalidation results. The pixels, exact-value predicate, submitted-effect predicate, admission authorization, execution, and release are synthetic or retained offline inputs. The experiment does not establish semantic grounding, live task success, real OS input safety, useful feedback, efficiency, or human-tempo benefit. Issue #57's integrated efficiency decision remains HOLD for matched live same-task/model measurements.

Task 3 is not an absence negative: the A14 review text says its Value field and Save button are absent, while the retained `inputs/054.png` visibly shows both. It was kept as an ordinary visible fixture; the negative controls are the pre-admission pixel replacements.
