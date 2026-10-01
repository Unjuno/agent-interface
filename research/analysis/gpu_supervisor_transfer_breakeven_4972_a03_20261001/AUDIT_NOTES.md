# Allocation-03 audit note

The candidate completed once with exit code 0. The independent CPU-only auditor completed once and returned HOLD_INTEGRITY with zero raw-data/parity errors, but only 4/5 corruption controls rejected.

The unsafe_admission control is a frozen no-op for this retained fixture: it assigns the first CUDA admission in batch-size 64, repetition 0 to 1, while the immutable raw value is already 1 (fresh_valid-0135, confidence 866, fresh sequence). The control therefore fails to exercise corruption detection. This is an auditor/test design defect, not a candidate contract mismatch. The allocation is consumed; do not modify the auditor, rerun either process, or upgrade the result. A future successor needs a mutation that flips a guaranteed-safe value (for example, select a retained row whose admission is 0 and set it to 1), then freeze that auditor under a new allocation.

Observed medians (ns) are retained in candidate_result.json but remain descriptive only because integrity did not pass. They show no apparent transfer-inclusive CUDA crossover on this device/workload; this is not a valid scoped PASS under the preregistered gate.

