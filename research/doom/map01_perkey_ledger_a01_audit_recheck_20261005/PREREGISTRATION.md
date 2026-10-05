# Per-key ledger A01 audit recheck

## H / T / D / C / U

**H:** The A01 raw-only auditor can accept stale candidate interval output after a timestamp mutation because it checks hard-coded bounds instead of deriving bounds from raw events.

**T:** Use the exact raw fixture and candidate output from PR #7701's frozen A01 package. First run the frozen auditor unchanged. Then mutate only the W interval's `release_sync_ns` and `up_sample_ns` by +1 ns while retaining the original candidate output. Finally run an additive independent auditor that reconstructs all expected intervals from raw timestamps and checks each candidate case.

**D:** The baseline auditor's mutation result is a defect if it exits 0 while the candidate still claims W upper bound 90 ns. The corrected auditor must pass unchanged data, reject the mutated raw plus stale output, and produce an expected W interval upper bound of 91 ns when paired with a freshly recomputed candidate output. Preserve candidate invocation count from the predecessor; do not rerun or rewrite its candidate output.

**C:** This only tests arithmetic audit integrity over one deterministic synthetic event fixture. Raw timestamps are authored and do not establish physical input timing.

**U:** No live X11/game/model/input, physical release, useful feedback, bounded recovery, task effect, or MAP01 outcome. The separate live lane remains unassigned; no allocation is inferred.
