# V39 paired-signal boundary construction A01

## H/T/D/C/U
- **H:** Current-main V39 paired health/ammo monitoring preserves a coherent usable pair, but fails closed when signal sequence/capture/binding diverges, either signal crosses its hard floor, or typed and full observations disagree for one epoch.
- **T:** Extract and execute the exact current-main helper/class definitions from `map01_overlap_controller_v39.py`; supply stub guard/reader interfaces only; evaluate nine frozen cases.
- **D:** Synthetic unit boundary matrix, no game, planner, or input device.
- **C:** Expected outcome fixed in `FROZEN.json` and candidate assertions before the container execution.
- **U:** A passing construction check says nothing about source-to-image capture integration, live event ordering, cancellation latency, physical key release, feedback usefulness, recovery, survival, progress, or MAP01 exit.

## Run
Run exactly once in WSLc container `python:3.12-slim`, network disabled, 1 CPU and 512 MiB. Raw output is `raw.json`. Source is pinned to `402c7d1b5147b2a905098f082233db60a47d68db`; the only commit after checked source snapshot `53ec001a334e4077caf665ff56372cd4b0ccb068` adds an unrelated `research/analysis/decision_value_calibration_7934_t0_a02_20261005/` package, confirmed by GitHub compare metadata.

## Audit
`audit.py` is an independent stdlib readback of the raw case set and expected outcomes. It does not invoke candidate code. No candidate retries are permitted; harness correction happened before the frozen run.
