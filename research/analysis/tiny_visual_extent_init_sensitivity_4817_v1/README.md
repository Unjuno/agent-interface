# Issue #4983 — fresh-init sensitivity diagnostic

This construction-only successor changes the CNN initialization seed on the exact #4850 data, model and optimizer schedule. Its immutable predecessor result remains unchanged. The runner performs the finite-difference gate before two 1,000-step fits; the independent CPU auditor regenerates the fixed data and directly recomputes logits. No formal fitting is authorized.

See FREEZE.json for exact source hashes, seeds, image, command and decision gates.