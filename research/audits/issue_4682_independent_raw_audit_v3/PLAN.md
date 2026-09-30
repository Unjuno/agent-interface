# Issue #4687 — independently verify retained #4682 evidence

This is a distinct raw-evidence allocation after #4682 stopped because its verifier could not locate the formal output. Preserve the #4682 package, formal invocation, STOP artifact and draft PR #4686 byte-for-byte. Do not rerun its formal runner.

## H / T / D / C / U

**H.** A separate local Docker verifier can independently reconcile the retained v2 formal AUDIT, host receipt, v2 freeze/source/input hashes, baseline, ledger controls and runtime mismatch controls when the formal artifact directory is mounted at the verifier's exact declared path.

**T.** Allocation `issue4682-independent-raw-audit-v3-20260927-01`; intake main `4011b8c8d83ecced9490b2e2f6ad60a2d62761e7`. Additive branch `research/issue4682-independent-raw-audit-v3-20260927`, path `research/audits/issue_4682_independent_raw_audit_v3/`. Copy the full v2 study, all immutable inputs, exact formal AUDIT and runtime receipt. Freeze verifier, tests, copied-artifact hashes and mounts before execution. Run construction tests in local Docker; then run exactly one independent raw-only Docker container with the v2 study/input, raw AUDIT at `/evidence/formal01/AUDIT.json`, runtime receipt, and v3 source read-only, and only a fresh output directory writable. Cached image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; `--pull=never --network none --read-only`, 1 CPU, 512 MiB, 32 PIDs. No v2 formal rerun, workflow, model/provider/GUI/input, or retries.

**D.** `PASS_INDEPENDENT_AUDIT_V3` only if all v2 source and input hashes reconcile, copied formal AUDIT and receipt match their frozen SHA-256 and each other, observed runtime equals frozen expectation, the raw baseline and three ledger controls match the retained outcome, all five runtime mismatch controls STOP before semantic audit, and this independent verifier emits zero errors. Any mismatch is `FAIL_RAW_EVIDENCE_MISMATCH`; missing source/image/mount is typed STOP. Preserve the first outcome; no rerun.

**C.** V3 path only; v2 and all predecessor records remain immutable. Local Docker only, offline and least-mounted. No other workspace containers touched.

**U.** One raw consistency verification of one retained synthetic audit/receipt. No recovery of #4649's unpublished ZIP, arbitrary auditor-completeness claim, other-platform validation or product/runtime claim.
