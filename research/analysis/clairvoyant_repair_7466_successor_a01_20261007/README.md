# Issue #8283 — corrected #7466 clairvoyant diagnostic

This read-only successor recomputes only the withdrawn A03 hindsight comparator. It does not rerun the A03 candidate or auditor, modify their source/receipts, or change the retained FAIL_UNSAFE_RESUME.

## Frozen question

- **H:** Under the actual one-work-unit-per-tick transition semantics, the corrected finite-horizon clairvoyant comparator has a strictly positive optimum on every retained A03 row, and every candidate-minus-oracle gap is nonnegative.
- **T:** Verify all six frozen source hashes, all three input hashes, compressed/raw candidate hashes, and the retained candidate-source receipt. Stream the 432 episode×cost rows from gzip, compute the constrained dynamic program from immutable public schedules/interruption labels, and report the 18 cohort×cost cells. Use only the standard library. Candidate/auditor invocation count added: zero.
- **D:** PASS_DIAGNOSTIC_REPAIR only if all identities match, 432 rows reconstruct, all retained oracle costs are positive, every gap is nonnegative, and four hand-checkable transition fixtures pass. Otherwise STOP without changing A03.
- **C:** The comparator is an unattainable hindsight diagnostic under stipulated synthetic costs. It cannot support an adaptive benefit claim or rescue incomplete/unsafe A03 rows.
- **U:** Synthetic method/data integrity only; no real interruption process, GUI, persistence, production safety, or latency claim.

## Recurrence

At tick t, state (p,d) means p work units have been reached and d units are durable. The oracle may either skip checkpointing or checkpoint iff legal[t] and p > d (incurring the frozen checkpoint cost and setting d=p). It then advances exactly one work unit. If the frozen interruption bit is set and the task is not yet complete, it incurs (p_after-d) × replay_cost and resets progress to d. There is no idle transition. For each equal-progress frontier, states dominated by another state with at least as much durable progress and no greater accumulated cost are removed; completed paths are retained as the best terminal cost.

Run python3 -B research/analysis/clairvoyant_repair_7466_successor_a01_20261007/repair.py on a fresh checkout with the predecessor A03 package available. It refuses to overwrite RESULT.json. Local checks:

- python3 -B -m unittest discover -s research/analysis/clairvoyant_repair_7466_successor_a01_20261007 -p 'test_*.py' -v
- python3 -m py_compile research/analysis/clairvoyant_repair_7466_successor_a01_20261007/*.py
- python3 research/analysis/check_index.py --strict
- git diff --check

The only inputs are immutable files under hazard_checkpoint_7466_feedback_gate_a03_20261004/. The analysis writes only its own RESULT.json.
