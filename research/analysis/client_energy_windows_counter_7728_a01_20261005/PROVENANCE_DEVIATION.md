# A01 runner-byte preservation deviation

The pre-run manifest records `run_preflight.ps1` SHA-256 `4285cb728ccddfe7ae4f82d6394630dcb668602061ac2fe72984f519b7cfe6b4`. That exact local hash was checked immediately before the one candidate invocation, so the sensor read was launched only after the recorded source verification passed.

Post-publication verification found that the committed Git blob for `run_preflight.ps1` hashes to `9e2048f4287aad0cedf055178b02775a4d02329e332e5b406fc45b0219364261`, not the frozen hash. The working-tree line-ending form also does not match the frozen hash. The original frozen runner bytes cannot currently be reconstructed from the retained commit. Preserve the raw counter bracket and independent audit unchanged; keep the measurement result `PASS_COUNTER_ORACLE_MATCH`, but record evidence custody as `HOLD_RUNNER_SOURCE_BYTES_UNRECOVERED`. No sensor rerun or freeze rewrite is made.

Package-local `*.json -text` now preserves the original CRLF/BOM JSON bytes in Git blobs, so raw-output and audit SHA-256 entries remain verifiable on non-Windows checkouts. This packaging correction cannot repair the missing exact runner bytes.
