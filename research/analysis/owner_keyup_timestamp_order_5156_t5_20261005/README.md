# Issue #5156 T5 — timestamp-order readiness guard

This additive construction package tests whether the offline retained-input analyzer refuses impossible ordering among its four timestamps. It follows #5156's T4 scoped finding and preserves T1–T4 artifacts unchanged. The baseline was frozen at `e561b25`; a later main advance to `b67fc4f` left the analyzer Git blob unchanged at `f3d5fe3`, so the T5 source change is on current main's descendant branch and does not alter allocation behavior.

## H/T/D/C/U

- **H:** readiness is true only when `admitted_ns <= input_ack_ns <= release_call_started_ns <= release_call_returned_ns`, allowing equality at boundaries.
- **T:** apply one frozen four-case corpus to the analyzer copied from current main before the repair, then to the repaired analyzer. The ordinary and all-equal rows must be ready; `ack_before_admission` and `release_return_before_start` must fail closed.
- **D:** baseline `FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED` reproduces the source defect. Repaired `PASS_ORDER_GATE_CONSTRUCTION_SCOPED` requires 4/4 expected classifications with no raw-integrity errors. These are analyzer-construction outcomes only.
- **C:** invalid timestamps may indicate collector corruption rather than a runtime ordering bug; the analyzer therefore rejects them as invalid release evidence, not as evidence of a physical release defect.
- **U:** no X11 server, game, GUI, model, GPU, OS input, or shared container was used. No physical key-up instant, input occupancy, application consumption, useful feedback, recovery, task effect, or MAP01 claim follows.

## Reproduction

Run the four-case corpus with each retained source and audit the output:

```powershell
python run_candidate.py --source baseline/analyze_map01_direct_retained_input_v1.py --phase baseline --out output/baseline_raw.json
python audit.py --cases cases.json --raw output/baseline_raw.json --source baseline/analyze_map01_direct_retained_input_v1.py --phase baseline --out output/baseline_audit.json
python run_candidate.py --source repaired/analyze_map01_direct_retained_input_v1.py --phase repaired --out output/repaired_raw.json
python audit.py --cases cases.json --raw output/repaired_raw.json --source repaired/analyze_map01_direct_retained_input_v1.py --phase repaired --out output/repaired_audit.json
python -m unittest research.doom.test_analyze_map01_direct_retained_input_v1 -v
```

## Scope and next gate

This repairs an offline readiness false acceptance found in T4; it does not satisfy #5156's separately gated X11 fixture allocation. That allocation still requires an explicit shared-container assignment. It also does not establish the wider r134 matched evidence for per-key admission/up/release, independently useful task feedback, and bounded recovery. The relevant live gates remain open.
