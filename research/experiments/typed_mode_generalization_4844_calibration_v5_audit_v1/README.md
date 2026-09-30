# Post-hoc audit of retained calibration allocation

This directory holds a separate raw-only audit attempt for #5198's preserved allocation-01 output. Its sole Docker invocation ended with exit code 0 but produced no retained `audit.json` and no captured stdout, so the attempt is recorded as `STOP_AUDIT_RECEIPT_MISSING`; no semantic audit result is claimed and the consumed audit is not retried. It does not replace the original `STOP_AUDITOR_IMPLEMENTATION_DEFECT`, rerun its frozen auditor, or regenerate formal output.

The intended audit input is immutable raw SHA-256 b55b8d9e58497c47ef5a2152d1236d27fdb6918a018cbeebf2a75f0b5f709470. The raw omits the preregistered unsafe-emissions fields, so that gate is not evaluable from the raw and must not be inferred as zero. See PLAN.md and FREEZE.json for protocol, hashes, and stop record.
