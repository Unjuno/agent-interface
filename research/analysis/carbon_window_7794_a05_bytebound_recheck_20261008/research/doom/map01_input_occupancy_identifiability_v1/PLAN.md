# MAP01 input-occupancy telemetry identifiability

## H/T/D/C/U

- **H:** The retained v39 trace cannot identify physical per-key held duration. It has key admissions and snapshots plus eventual verified-empty program releases, but no key-specific release timestamp.
- **T:** Parse the exact retained v39 `runtime/events.jsonl`; report event counts and release evidence. Run synthetic positive/negative controls for the analyzer.
- **D:** Frozen input is `research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl` at current main `cdfebdb125e0566d2cbe741c4925b94eb17b439b`. Source blob identity and SHA-256 are recorded in `RESULT.json` after execution.
- **C:** PASS only if the immutable raw counts match the observed stream (634 rows; 39 admissions; 28 `keys_held`; 9 terminal releases all verified empty; one `input_released` verified empty), per-key release count is zero, positive control is detected, and controls missing key identity or time are rejected.
- **U:** This does not infer when individual physical keys went up, estimate occupancy duration, establish live controller behavior, or replace a new instrumented allocation. It identifies a telemetry gap in the retained run only.

## Procedure

1. Run `python analyze.py` against the retained trace.
2. Run `python -m unittest -v test_analyze.py`.
3. Independently recalculate counts and inspect raw release records; do not modify or replay the source run.
