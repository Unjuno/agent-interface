# Issue #8157 formal A02 result

**Disposition: `FAIL_METHOD` under the preregistered integrity gate; scientific outcome unscorable.** The candidate completed once with exit 0 and produced 200 sequence rows / 2,400 prefix estimates. The independent auditor completed once with exit 2 and reported 98 reconstruction mismatches, all confined to the occlusion profile. Diagnosis identifies a future-information check in the auditor that incorrectly invalidates earlier prefixes. The first candidate output and first auditor report remain unchanged; neither role was retried.

The saved auditor report records interval containment and mutation checks as passing, but candidate reconstruction failed. Its threshold and outcome metrics are not scientifically interpretable after that integrity failure. No claim is made that the method passes or fails on its scientific hypothesis. The next admissible step is a separately frozen successor allocation with a corrected auditor, if authorized under #8157's one-shot rule.

Execution used the exact pinned Python arm64 image in an isolated, network-disabled OrbStack container on macOS. The candidate mounted only its source file and public measurements; the oracle remained in an isolated directory and was mounted read-only only for the auditor. The run is synthetic-only with no GUI, model, game, user data, input, or runtime integration.

See `RUN_RECORD.json`, `DIAGNOSIS.md`, `RUN_FREEZE.json`, `SOURCE_SHA256.txt`, `INPUT_SHA256.txt`, `CANDIDATE_SHA256.txt`, `candidate/candidate.jsonl`, and `audit/REPORT.json`.
