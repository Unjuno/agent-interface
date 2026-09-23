# STOP

Decision: STOP_EXPECTATION_COUNT_MISMATCH

The single Docker formal invocation used python:3.12-slim and produced:
- rows=256
- accepted=8
- expected_accepted=8
- mismatches=0
- authority_true_admitted=0
- raw SHA-256: 55aa481950f438640ac0891fa581ff3dd519f79b6fbae4fbd9ccbfaa87193dc9

The harness asserted accepted=16, so the process exited nonzero. This is a preregistration/counting error, not a contract mismatch: the independent expected predicate agreed for all 256 rows. No rerun, tuning, source repair, model, GUI, network, runtime, or task input occurred under identity #2046.

A count repair requires a fresh successor identity. Parent #2009 remains unchanged.
