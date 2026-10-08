# Exact-crop cache memory-bound construction diagnostic

Issue: https://github.com/Unjuno/agent-interface/issues/5254  
Successor to: #4083  
Allocation: `exact-crop-cache-memory-bound-4083-20260928-01`  
Intake main: `0a69b1e273b434c05950e528e08ffcec44823885`  
Branch/path: `research/exact-crop-cache-memory-bound-4083-v1-20260928` / `research/measurement/exact_crop_cache_memory_bound_4083_v1/`

## Construction-only first result

On Windows 11 (build 26200), CPython 3.12.10, NumPy 2.4.2 and Pillow 11.3.0, the excluded host construction exercised the pinned #4083 cache implementation on ten deterministic 80×60 RGB PNGs, followed by revisits to the final two identities; LRU capacity was two frames. All 12 direct, unbounded-cache and bounded-LRU score objects matched. The unbounded cache retained 144,000 RGB-pixel bytes, while the bounded cache retained exactly 28,800 bytes (2 × 80 × 60 × 3); both final revisits were cache hits. The separate auditor reported 108 checks, zero errors and 4/4 effective corruption controls: `PASS_CONSTRUCTION_SCOPED`.

This is only a reduced host construction check. It is not the frozen 64-version/800×600 formal workload, not a Docker execution, not a process-RSS limit, and not evidence of full-app memory use or performance. Formal invocations: 0. The shared Docker lane remains unassigned; no Docker command was issued.

The first auditor construction exposed a vacuous occupancy mutation and rejected only 3/4 controls. That construction failure is recorded in `CONSTRUCTION_AUDIT_FAILED_INITIAL.json`. The raw runner bytes were identical on the final successful construction (SHA-256 `9910b4f8011c79ada7ec86144102960576f250593992bbee4e835cfa945b8e14`); the audit mutation was corrected before any formal freeze or invocation.

## Source identity

The reused implementation was fetched directly from its published GitHub branch and upstream main at these exact Git blob IDs:

- #4083 `candidate.py`: `993d983e05ddcd2a089cd8e63fa4a292b057b137`
- `exact_crop_semantic_probe_v1.py`: `22a5c022d613039b0386535304cbc432009699af`
- `inkscape_selection_frame_probe_v1.py`: `f4a68e95e6bbeb2896a00168f0c88282551be4e4`

Construction runner: `study.py` (SHA-256 `7ebcbadc02294143a4db7fc3d360b62faf028075c8a0764a37cdb9e0d91dbac6`).  
Independent auditor: `audit.py` (SHA-256 `e58aa526515dbfc89ea8aaf9dc724480dc79ed3244652b422e734522baa0f30c`).  
Raw: `construction.json` (SHA-256 `9910b4f8011c79ada7ec86144102960576f250593992bbee4e835cfa945b8e14`).  
Audit: `audit.json` (SHA-256 `aefaddca5d6161f3008a67c9e490d3a1c6d39bfdcc103416ff1ef945d15065ce`).

Reproduce the construction commands from this directory:

```powershell
python -B study.py construction.json
python -B audit.py construction.json audit.json
```

The formal path remains gated on a fresh exact shared-resource assignment, latest-main/source/image/output checks, publication readback, and a single runner followed by its separate raw-only auditor. Do not retry or reuse this construction as formal evidence.

