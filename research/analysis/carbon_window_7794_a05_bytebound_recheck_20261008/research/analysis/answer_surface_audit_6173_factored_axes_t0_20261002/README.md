# Factorized answer-surface evidence successor

The fixture keeps candidate-visible events and observer-side events as distinct fields. The candidate sees only the former; the raw-only auditor reconstructs the attempt, acquisition, coverage, and derived disposition axes from the latter and verifies the join.

Run construction tests with python3 -B -m unittest -v test_axes test_audit_axes. After verifying FREEZE.json, run candidate once with python3 -B run_candidate.py, then run python3 -B run_audit.py once only if the candidate exits 0.

All traces and answer artifacts are synthetic canaries. No real answer, model, user data, GitHub/web retrieval, network, app, GUI, or physical input is used. No container is created or entered.
