# Construction / postformal audit notes

- Preflight verified the exact Docker Desktop server, cached image ID/platform, six Git blob IDs, and source hashes. No existing output directory was present.
- Container 1 ran once and exited 0: all five `StrictAuditTests` passed.
- Container 2 ran once and exited 0: the raw-only CLI returned `PASS_OFFLINE_STRUCTURAL_AUDIT`, errors `[]`, and all 21 corruption controls were rejected.
- The frozen PowerShell wrapper then exited nonzero at its host-side output assertion. Root cause: PowerShell deserializes `corruption_controls_rejected` as a `PSCustomObject`; `.Count` yields a scalar value per property (1), not the number of JSON map properties (21). This is a verifier/orchestration defect after both container executions, not a container or candidate audit failure.
- No Docker container, unit test, or CLI was rerun. The formal logs, exit receipts, and output JSON are retained byte-for-byte. A separate posthoc read-only verifier evaluates them without invoking Docker or candidate code; see `posthoc_verify.py` and `results/formal01/verification-posthoc.json`.
- First posthoc verifier construction pass undercounted the verbose unittest lines due to an overly narrow regex; this affected only the posthoc script, not the immutable Docker logs or test execution. The parser was corrected to the exact unittest verbose format before the retained posthoc verification report was accepted. No formal command was repeated.
