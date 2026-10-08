# First-rung corrected lifecycle pilot — scoped PASS

Allocation `needle-role-skill-lifecycle-4916-first-rung-20260928-02` has a
frozen hypothesis and gates in `FREEZE.json`, preregistered on Issue #5053.
The corrected pure-Python scorer passed its one-shot OrbStack Docker
construction suite (four tests, including 12,288/12,288 retained predictions;
exit 0). The one-shot formal run then completed five paired AB/BA blocks,
40 requests per arm per block (400 predictions total). The raw-only independent
auditor recomputed all predictions and rejected all seven declared mutations.
Its disposition is `PASS_LIFECYCLE_FIRST_RUNG_SCOPED`.

Reuse won all 5/5 blocks. The median total reuse-to-reload lifetime ratio was
0.0300457 (about 3.0% of reload cost; about 33.3x lower for this implementation
and setup). Individual block ratios were 0.0244, 0.3024, 0.0300, 0.0284, and
0.2838, showing substantial variability in measured initialization cost. Do
not interpret the median as a general workload speedup or production latency.

The launch precheck observed another short-lived container
(`relaxed_gates`, image `concentration-aware-ns:checker`). It was not stopped or
modified. Its owner confirmed the compile/check had finished and released the
lane before formal timing began; `docker ps` was empty at formal and audit
invocation. The construction receipt remains exact correctness evidence and
the formal timing is separately retained; allocation -02 was not retried.

The preceding parity diagnostic independently recomputed all 12,288 rows and
found zero mismatches after correcting the rank-by-output B matrix orientation;
see `../needle_role_skill_lifecycle_4916_parity_diag_v1/` and the linked Issue
comments. This pilot measures only read/parse/validation/construction lifecycle
under the frozen pure-Python scorer and cached linux/amd64 image. It does not
measure PyTorch/framework execution, learned-skill efficacy, broad workloads,
GUI/task effect, or product latency; it does not close #4916. A separately
frozen larger run is required for any broader performance claim.

The detailed construction, formal raw output, audit and their hashes are in
`results/construction-02/`, `results/formal-02/`, and `results/audit-02/`.
The exact commands and frozen source/input identities are in `FREEZE.json`.
