# Allocation A01 — frozen-source mismatch STOP

## H / T / D / C / U

- **H:** A current-main-bound frozen-source gate prevents the synthetic candidate from starting when any frozen byte identity disagrees.
- **T:** Allocation `ISSUE5730-FAIL-CLOSED-CONSTRUCTION-A01-20261001`; source main `24f6b7d5f9395105807f981d48db212e6692a6f4`. The preregistered 14-case host-only construction suite ran once and passed 14/14. The separate synthetic formal wrapper was invoked once against the frozen manifest.
- **D:** `STOP_FROZEN_SOURCE_MISMATCH:synthetic_candidate.py`. Manifest expected SHA-256 `facc18ffecc66254a1f604c7ca8c8656330665273f327e8e5ff61958b72ba46f`; actual frozen candidate SHA-256 `facc18ffefc66254a1f604c7ca8c8656330665273f327e8e5ff61958b72ba46f`. Wrapper exit 1. Formal candidate=0, formal auditor=0, Docker/OrbStack=0, GPU/CUDA/model=0, retries=0. `evidence/formal-01` was not created; raw candidate SHA is null. Scientific result is `NOT_EVALUATED`.
- **C:** Windows 11 host, CPython 3.11.9, standard library only. The test suite's success, rejection, and one real-child-process cases are synthetic construction controls; they are not the separate frozen formal allocation, GPU test, or scientific evidence.
- **U:** No conclusion about GPU arithmetic/performance, live threat control, actual device contention, or power-loss durability. The frozen mismatch STOP is preserved; the A01 allocation will not be retried or silently corrected.

## Exact execution record

1. `python -B -m unittest -v test_fail_closed.py` — exit 0; 14/14 passed; stdout 0 bytes (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`); stderr 2,278 bytes (SHA-256 `8bc1d4d90c99f8660271ff9ca5ac5904fef4b71a9d943f458d1d06c0e519ad75`).
2. `python -B run_construction.py --freeze FREEZE.json --output evidence/formal-01` — exit 1; stdout 0 bytes (same empty SHA); stderr 52 bytes (SHA-256 `6f4ee9531f5cec7e4e51ae3117251ce7d9aa70810827357ad5211fe42822ec77`). Candidate did not start.

Retained raw stdout/stderr files are under `evidence/`; their bytes and hashes are unchanged. This STOP is protocol evidence only and must not be represented as a PASS/FAIL for the scientific hypothesis.
