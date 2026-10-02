# #6590 T1 training-implementation successor

This package is a new, source-separated successor to the retained v1 allocation. It repairs the v1 frozen candidate's missing first-layer update (`w1 -= learning_rate * dw1`) and first tests that the candidate's 250-step construction fit is byte-identical to an independently coded raw auditor refit. The v1 source, failed formal output and issue history remain immutable.

The first v2 prelaunch (`training-parity-20261002-01`) STOPped before container creation because `main` advanced from frozen `2089690` to `cc67052` with only new Issue #6530 package paths. Counts were candidate fits 0, auditor fits 0, containers 0, retries 0. `results/prelaunch-01/STOP.json` preserves the exact reason. The follow-on runner permits disjoint main advances only when the frozen main remains an ancestor and no protected goal/roadmap/README, predecessor, package or workflow path changed; the run record captures those intervening paths. No scientific input or consumed seed is changed.

The second prelaunch (`training-parity-20261002-02`) STOPped on `KeyError: docker_context` because the runner read runtime identity at the wrong freeze level. Again counts are candidate fits 0, auditor fits 0, containers 0, retries 0; exact STOP is in `results/prelaunch-02/STOP.json`. A ninth construction test now explicitly validates the nested runtime schema the runner consumes before a third preflight.

## H / T / D / C / U

- **H:** The corrected candidate updates W1 and byte-matches the independent full-batch MLP refit for identical frozen rows, initialization, float32 learning rate and step count.
- **T:** Reconstruct one balanced 160-row synthetic training set. Starting from a known seed, run the frozen 250-step update schedule once in candidate and once in independent auditor; require nonzero W1 delta, all four parameter arrays byte-identical, and same digest. Run this as construction validation in a network-none pinned OrbStack container, with no evaluation labels or model-effect claim.
- **D:** `PASS_TRAINING_IMPLEMENTATION_REPRODUCIBLE` iff data hashes match, W1 changes from initialization, all arrays/digest match exactly, and adversarial omission of the W1 update is rejected by the test. Any mismatch is `HOLD_TRAINING_IMPLEMENTATION`; environment/provenance failures are STOP. This gate does not decide #6590's spatial-block hypothesis.
- **C:** Identical deterministic data, image, seed, NumPy and single-thread OpenBLAS within one pinned runtime. Candidate/auditor implementations remain separate modules. W1-update mutation is the explicit negative control.
- **U:** A construction PASS establishes only implementation parity for one synthetic fit recipe, not model competence, spatial generalization, effect, safety, GUI robustness or product utility. The v1 10-fit allocation is consumed and never rerun.

The combined freeze authorized one subsequent fresh-seed formal allocation only after construction PASS. That allocation completed as **`H_FAIL_SCOPED`**; see [`REPORT.md`](REPORT.md) and `results/formal-03/`. The retained predecessor v1 result and both v2 prelaunch STOP records remain unchanged.

## Reproduction

The container image, frozen input, run command, output, stdout/stderr and auditor receipt are recorded in `FREEZE.json` and `results/`. Both construction and formal containers are network-disabled, CPU-only, source-read-only and resource-bounded. The test module can also be run locally with `python3 -B -m unittest discover -s research/analysis/spatial_block_position_6590_t1_orbstack_v2 -p 'test_*.py' -v`.
