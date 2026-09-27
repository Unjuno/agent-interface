Date: 2026-09-20 Asia/Tokyo
Source: main O3 evaluator/test files at current refs.
Command: docker run --rm --network none -v /tmp/o3main:/workspace:ro -w /workspace --entrypoint python3 python:3.12-slim-bookworm -m unittest research.observation_gating.o3_relevant_region_successor_v1.test_gate
Result: PASS_O3_GATE_PREFLIGHT_SCOPED; 3 tests passed.
Hashes: SCOPE.md d810c29be9f6c161ff07bb79b8a657102f1c0e5e82d72413c402b49fc7edea5d; gate.py 59dfdc4b44b13f0ca4cfac8fa063d6b4bc1d193e08b9ab4351f9636ed1917ad3; test_gate.py 15cdc20ddd0877214a362dbbfe6623603936639161218ededab177501a0d130b.
Boundary: pure evaluator preflight only. #2811 live GUI transport, capture/arrival timestamps, effect binding, model package, and live task correctness remain unverified.
