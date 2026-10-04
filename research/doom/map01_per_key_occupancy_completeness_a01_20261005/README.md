# MAP01 per-key completeness construction A01

This offline construction test found a completeness gap in the retained per-key occupancy ledger. With the two-key synthetic fixture, deleting the `SPACE` interval while retaining `W` and the verified-empty receipt still yields `BOUNDED` from the legacy ledger. The test-only wrapper with frozen expected inventory `{SPACE, W}` preserves the complete case's exact bounds and returns `UNKNOWN` for the omission. Four unit tests passed; an independent raw-only audit separately reconstructed the full and omitted cases and passed five checks.

## Evidence

- `PREREGISTRATION.md` records H/T/D/C/U and decision rules.
- `FREEZE.json` binds the selected current-main reference, source blobs, raw bytes, candidate, test, and preregistration hashes before the candidate tests ran.
- `audit_v2.py` and `AUDIT_V2_FREEZE.json` are retained as historical audit artifacts. Review found that v2 reported, but did not enforce, its raw-fixture digest and hard-coded the expected inventory.
- `audit_v3.py` and `AUDIT_V3_FREEZE.json` are the active independent audit. Before reconstruction, v3 enforces both frozen SHA-256 pins and validates the unique, non-empty expected-key inventory loaded from the freeze. It imports neither candidate nor legacy implementation. `test_audit_v3.py` exercises raw-byte tampering, source tampering, and invalid inventories.
- `audit-result-v3.json` is the active audit output; it passed eight checks. `audit-result-v2.json` remains unchanged as historical evidence, while `audit-result.json` remains audit v1.
- `ledger.py` and `raw.json` are exact copies of the retained main artifacts. `SOURCE_BLOBS.json` binds their repository blob IDs at selected main.
- `COMMANDS.txt` records the executed commands. Candidate tests returned exit 0 (4/4 passed); v3 audit tests plus candidate tests returned exit 0 (8/8 passed); audit v3 returned exit 0 (`PASS_METHOD_SCOPED`).
- `test-output-integration.txt`, `audit-output-integration.txt`, and their exit-code files record a second validation after copying the package onto the clean main-based handoff branch; it again returned 4/4 and `PASS_METHOD_SCOPED`.

## H/T/D/C/U

**H:** The retained ledger lacks an expected-key completeness invariant and can report a partial action as bounded. A completeness gate with a predeclared expected key set should reject that omitted-row case while preserving complete bounds.

**T:** Apply one deterministic omission mutation to the retained two-key raw fixture; compare the legacy ledger and the wrapper, then independently reconstruct both.

**D:** PASS_METHOD_SCOPED required complete-case bounds to remain `SPACE=32..50 ns` and `W=70..90 ns`, legacy omission to remain accepted (counterexample), gated omission to become `UNKNOWN`, and the independent audit to agree.

**C:** This synthetic row deletion does not model real X server input, application event consumption, or a naturally missing telemetry event. A caller could also supply a wrong expected-key inventory.

**U:** One deterministic construction case only. It does not establish real key occupancy, application delivery, independently useful task feedback, bounded recovery efficacy, task effect, MAP01 completion, safety, human tempo, or latency benefit.

No game, model, GUI, input, GPU, container, or network workload was started. This result does not authorize the separately gated #59 live allocation.
