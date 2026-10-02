# Successor #6689 S03 result

- Allocation: PREFIX-STABILITY-6689-S03-WSLC-20261003-01
- Issue: #6809; branch: research/prefix-stability-6689-successor-s03-rebased-20261003
- Base: main at aeae0edea4e3aba67329e524abd5901b3602dd02; additive successor branch created from this exact SHA.
- Runtime: WSLc, python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 (local RepoDigest confirmed); Python 3.12.15; --pull never --network none --cpus 1 --rm. Candidate, independent baseline auditor, and mutation controls each ran in a separate container.
- GPU: not used; this finite stdlib state-machine fixture has no GPU-accelerated computation.
- Baseline: PASS, 5/5 rows independently reconstructed.
- Mutation controls: PASS, 5/5 rejected (remove pending obligation, corrupt counts, drop row, false-finalize, relabel trace).
- No retries. WSLc had no running containers immediately before allocation; each invocation used --rm.
- Scope: authored five-case finite state machine only. This does not validate any production system or historical #6689 run.
- Raw output: candidate_stdout.json, audit_stdout.json, mutation_stdout.json. Procedure/source are in PLAN.md and the scripts in this directory.
