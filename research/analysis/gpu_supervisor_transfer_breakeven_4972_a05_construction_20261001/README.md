# Allocation-05 CPU construction: unsafe-admission corruption control

## H / T / D / C / U

**H.** A corrected negative control for allocation-03's retained auditor defect should always change a known-safe admission bit from 0 to 1, and should fail closed if no 0 exists.

**T.** Extracted the proposed helper from the allocation-03 audit note and exercised deterministic positive fixtures plus an all-ones negative fixture. The same Python source retained at `research/analysis/gpu_supervisor_transfer_breakeven_4972_a05_construction_20261001/test_unsafe_admission_control.py` was piped to `python -` on the Windows host. No candidate result, timings, CUDA call, model, GUI, input, container, network, or live allocation was used.

**D.** Exit 0; all 3 checks passed: select and flip the first 0 in `[1,0,0]`; select and flip the first 0 in `[0,1]`; reject `[1,1]` with `ValueError`. This verifies only the isolated mutation helper. It does not execute the full raw auditor against a synthetic candidate or establish that all five corruption controls reject.

**C.** Local Windows Python; CPU-only deterministic fixtures. Current C: free space was about 5.7 GB at this work segment; host RTX 3080 remained idle. The exact-source test execution used a PowerShell here-string piped to Python, followed by the identical source being retained on the GitHub branch.

**U.** No formal allocation-04/05 GPU candidate or auditor invocation; allocation-03 remains immutable `HOLD_INTEGRITY`. No CPU/CUDA parity, crossover, scientific, or performance result is claimed. This is construction evidence only; a fresh current-main source freeze and exclusive GPU assignment are still required.

## Reproduction

`python test_unsafe_admission_control.py`

Expected: `PASS 3/3: mutation flips a zero; no safe value fails closed`
