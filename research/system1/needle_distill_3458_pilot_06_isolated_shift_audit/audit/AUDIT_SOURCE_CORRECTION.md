# Post-formal audit-source correction

The first independent audit attempt is preserved unchanged as `AUDIT_ATTEMPT_01_STOP.json`. It reported 6,156 errors and exited nonzero; this is an auditor STOP, not a model result and not a second formal run.

Two defects were isolated in the frozen auditor:

1. Baseline controls were reconstructed by re-seeding and generating a different row count for each individual row. PyTorch CPU random streams are shape-sensitive, so these values did not reproduce the original 1,024-row generator call. The corrected auditor independently regenerates the complete 1,024-row class array from the preregistered seed, then compares each retained control row in class order.
2. Invalid-control inputs are float32 tensors serialized as Python floats. The frozen auditor compared these exactly to ideal decimal float64 literals, causing expected float32 representations (e.g. 0.20000000298) to fail. The corrected auditor compares finite coordinates within 1e-6, requires the exact metadata/case, and checks the explicit `"NaN"` sentinel separately before independently recomputing the yield reason.
3. Final audit hardening independently recomputes the deterministic boundary reason from each retained boundary input (and validates finite six-dimensional input shape); the first two audit outputs checked the reported reason/count but did not independently prove that each input was a boundary case. These prior outputs remain preserved as intermediate audit artifacts.

Frozen preformal auditor SHA-256: `57d966ac6c5f4ec8f8905b4df378465cf5ea126171ee0fdde3687118e8db2920`. Corrected postformal auditor SHA-256: `8bf76f29cde62b5f685116427ba6524e0792cec7eec4ad8a447873c724501b7b`. The formal runner is unchanged at its frozen SHA-256 `0a1900f6125c0b3a253cac56b88459b43e48fe0104290273151b8697eef4f20e`; raw formal SHA-256 remains `0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7`. No formal bytes, source allocation, threshold, seed, model, or predictions were changed or rerun. The initial STOP and intermediate corrected audit remain retained. Even with a clean final audit, any preregistered numerical gate miss remains a FAIL.
