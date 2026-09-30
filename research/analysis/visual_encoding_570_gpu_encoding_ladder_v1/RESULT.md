# Issue #4738 result — GPU encoding ladder

Allocation: visual-encoding-570-grid-context-r5-20260927-01
Branch: research/visual-encoding-570-grid-context-20260927
Model: qwen2.5vl:3b, Q4_K_M, digest fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1
Runtime: RTX 3080 Laptop, Ollama 0.34.4 in pinned linux/amd64 Docker image; 60 sequential requests, zero retries.

## Result

All 60 requests completed and the independent audit reports `REJECT_NO_MATERIAL_ENCODING_GAIN` with no integrity errors. RAW detected 10/10 present targets; all five arms abstained on both absent targets. BORDER_RULER detected 9/10; COARSE_GRID and CONTEXT_CROP each detected 6/10; GRID_CONTEXT detected 5/10. The qualifying encodings set is empty. No added representation improved the preregistered outcome over RAW.

The GPU sampler captured  active samples during inference; see GPU_SUMMARY.json for utilization and memory. (GPU placement was independently validated per request by overlapping samples and `ollama ps` reporting GPU.)

## Interpretation boundary

This is a small synthetic-screen test of one cached 3B quantized model on one RTX 3080 Laptop. It does not establish general model, real-app, or GPU speed claims. Do not promote these encodings based on this run. Preserve the result as a negative successor experiment; any follow-up should use a fresh allocation and separately preregistered screens/model.

## Evidence

- `FREEZE.json`: protocol, exact artifact identities, and source hashes.
- `README.md`: H/T/D/C/U and execution boundary.
- `audit/AUDIT.json`: independent per-case audit and decision.
- `ARM_SUMMARY.csv`: compact arm-level metrics.
- `GPU_SUMMARY.json`: GPU sampler summary.
- `evidence/CONSTRUCTION_AUDIT.json`: preformal input-construction audit.
