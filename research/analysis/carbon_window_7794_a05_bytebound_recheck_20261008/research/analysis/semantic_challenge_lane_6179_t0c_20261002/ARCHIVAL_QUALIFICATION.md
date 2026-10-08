# Qualified preservation of the terminal T0c allocation

This directory preserves Issue #6477 / PR #6489 at published head `018d466216283b1f4350b75d1aa66537304c8264`. Its disposition remains `STOP_PRE_FORMAL_ONE_SHOT_CANDIDATE_BUDGET_CONSUMED_OUTSIDE_WSLc`. It is not a formal WSLc result or scientific PASS/FAIL. All nine original allocation files remain unchanged.

A mistaken standalone Windows-host invocation, `python candidate.py --help`, executed the candidate and treated `--help` as the output filename. Retained HOST_DIAGNOSTIC_CANDIDATE_RAW.json contains 18 rows and is 58,960 bytes. The historical record reports SHA-256 `9d656fcd8cab175353054fd7dcefabc2b084ea2ec6678ba1efbf1b149f8d62b1`; this review did not recompute it. The host invocation consumed the one-shot candidate budget. Formal WSLc construction/candidate/auditor counts remain 0/0/0, with zero retries.

Two host invocations of the WSLc-only construction gate stopped at memory.max=MISSING, exit 2, before tests and created no containers. Recorded 9/9 host tests and synthetic 18-row, zero-error round-trip audit are development-only diagnostics. Zero formal candidate invocations must not be described as zero host candidate execution.

The original README, preregistration, protocol, source, tests, raw and terminal record are historical evidence. Their prospective instructions do not authorize restarting this consumed allocation. No construction suite, candidate, auditor, diagnostic, hash recomputation or resource operation was run for preservation.

This published bundle contains no formal freeze, WSLc raw, independent formal audit report or complete execution transcript. Statements about prior commands and outcomes are retained reports, not newly reproduced verification. Missing evidence is not reconstructed.

Earlier resource-ownership uncertainty is historical context; the final candidate-budget STOP is controlling. Separate #6471 does not change T0c; #6179 HOLD and #6461/T0b STOP remain unchanged. Preservation establishes no production verifier reliability, cryptographic security, tenant/process isolation, unknown-fault coverage, GUI safety or field reliability. Issue #6477 remains open.
