# Issue #5547 history-closure successor — STOP

Allocation: `ic-history-closure-5547-20261001-02`  
Frozen source main: `2b2166da7e1e3b4e60e435b6c7857484797a23ec`  
Current main at publication check: `b71815e492a810ebee964adbbdc04bf391b30600`  
Disposition: `STOP_FROZEN_EXPECTATION_MISMATCH`; no scientific pass/fail claim.

## H / T / D / C / U

- **H:** A root-only checker must not certify a precondition-disabled COMMIT as safe; reachable closure may expose a duplicate semantic effect after authorization, while the serial baseline rejects the second commit.
- **T:** One frozen host-CPU test suite, one runner, one independent raw audit with five frozen mutation controls. No retries or altered expected values.
- **D:** Frozen expected values were 5 reachable states, 42 ordered pair rows, and 2 counterexamples. The single runner produced 6 states, 48 rows, and 4 counterexamples, while finding the expected witness. The independent audit exited 1 with `frozen_reference_matrix`, `enumeration_completeness`, and `state_count`; it rejected all 5/5 corruptions. This allocation stops at the preregistered mismatch. Do not reinterpret or tune expected counts and do not rerun.
- **C:** Windows CPython 3.11.9, stdlib only, host CPU. No Docker, GPU, CUDA, model, network, or external effect.
- **U:** Candidate finite-model behavior remains unaudited against the frozen expected matrix. No general I-confluence, runtime safety, or coordination-cost claim is made.

The six frozen unit tests passed. That does not override the failed raw audit. All six frozen source hashes in `FREEZE.json` were read-only rechecked and match. Raw output and failed audit are retained unchanged. `#5139` remains separately gated; this CPU-only work neither requests nor implies its GPU/Docker lease.
