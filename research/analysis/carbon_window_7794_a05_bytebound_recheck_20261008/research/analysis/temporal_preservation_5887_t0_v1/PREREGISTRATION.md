# Frozen T0 preregistration — Issue #5887

Allocation: `TEMPORAL-PRESERVATION-5887-T0-20261001-01`
Planning main: `7dbe196b8d1fb519139d15240ecb3f377a07b51d`
Candidate/auditor image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, local image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/amd64.
Execution: local Docker Desktop `desktop-linux`; network none; read-only root, bounded tmpfs; candidate once, then independent raw-only audit once if candidate exits 0. No retries.
Oracle frozen before candidate: exact-repeat coalescing merges only adjacent rows with equality over all typed required semantic fields and identity generations and no edges. Thus benign full-valued stutter preserves; latest-state deletion of transient warning, focus loss/recovery, or generation transition is NOT_PRESERVED; pixel-only equality must not certify authority/generation equivalence; edge reordering is NOT_PRESERVED; missing timestamp or uncovered interval is UNKNOWN.
Pass requires identity/exact projection preservation on the benign case, counterexamples for each harmful projection, event-order detection, and UNKNOWN for timing/coverage gaps. This is a finite synthetic method test only.
