# Successor #6689 S03 result

- Allocation: PREFIX-STABILITY-6689-S03-WSLC-20261003-01
- Issue: #6809; branch: research/prefix-stability-6689-successor-s03-20261003
- Base: main at 37b973cd28e20b52950f6e5b75668b76f5d4bd65 (confirm current base before merge)
- Runtime: WSLc, python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016; Python 3.12.15; --pull never --network none --cpus 1 --rm. Separate candidate, baseline auditor, mutation-control containers.
- GPU: not used; finite stdlib state-machine fixture does not benefit from GPU.
- Baseline: PASS, 5/5 rows independently reconstructed.
- Mutation controls: PASS, 5/5 rejected (remove pending obligation, corrupt counts, drop row, false-finalize, relabel trace).
- No retries. WSLc had no running containers immediately before allocation; after each --rm invocation no workload retained.
- Scope: authored five-case finite state machine only. This does not validate any production system or historical #6689 run.
- Evidence: output reproduced in PR body and immutable artifact files to follow.
