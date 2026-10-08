# Issue #4983 — fresh-init sensitivity diagnostic

This construction-only successor changes the CNN initialization seed on the exact #4850 data, model and optimizer schedule. Its immutable predecessor result remains unchanged. The runner performs the finite-difference gate before two 1,000-step fits; the independent CPU auditor regenerates the fixed data and directly recomputes logits. No formal fitting is authorized.

See FREEZE.json for exact source hashes, seeds, image, command and decision gates.
Construction outcome: [report](construction_01/REPORT.md), [raw result](construction_01/RAW.json), [independent audit](construction_01/AUDIT.json), [corruption controls](construction_01/CONTROL_RESULTS.json), [checksums](construction_01/SHA256SUMS.txt), and [execution receipt](construction_01/EXECUTION.json).
