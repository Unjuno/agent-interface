# Construction-only record (not formal)

- Host: Windows, CPython 3.11.9; no WSLc/container, GPU, GUI, model, or external network was used.
- Command: `python run_construction.py fixture.json candidate.py auditor.py construction-02`; then `python mutation_t0.py fixture.json candidate.py auditor.py`.
- Candidate and independent raw-only auditor: 32 rows, zero errors, `PASS_METHOD_SCOPED`.
- Five mutations rejected: drop row, false capture, target-loss continuation, lease violation, false effect.
- On constant motion, fixed captured at ticks 0–5 (6 captures); triggered captured only at tick 0 (1 capture), both exact effect. On reversal, fixed captured 6 times; triggered captured at ticks 0 and 3 (2 captures), both exact effect. Nonpredictive sample-hold missed the reversal.
- This is local construction evidence for an authored finite fixture, not the formal Issue result. The residual source equals the fixture's synthetic target-position stream and may be much more informative than an actual visual residual; costs are operation counts, not measured latency.
- Earlier pre-freeze attempts: attempt 01 used the next tick's target for terminal scoring and falsely failed two controls; a subsequent sensor-refactor run stopped with an auditor `KeyError` for a removed residual field. Both were fixed before the retained construction-02 run. No formal candidate/auditor budget was consumed.
