# WSLc portability successor for Issue #6315

## Disposition

`PASS_RUNTIME_PORTABILITY_SCOPED` for the exact finite synthetic workload from PR #6333. The frozen candidate ran once in WSLc and emitted byte-identical candidate raw to the prior OrbStack/Docker run. A separate raw-only auditor ran once, reconstructed all 14 case/mode outcomes, and rejected all four frozen mutations. The new result supports substituting WSLc for this particular local CPU/single-container workload.

The predecessor's original auditor defect remains intact in PR #6333 and Issue #6315; this successor neither edits nor relabels that historical `HOLD_AUDIT_IMPLEMENTATION` record.

This does **not** show faster iteration, lower peak memory, effective memory limits, broad Docker parity, or application/product benefit. No Docker Desktop process or service was observed or started for this run.

## H / T / D / C / U

- **H:** The exact Issue #6315 candidate and fixture can run on this Windows host through WSLc with network disabled, read-only inputs, separate writable output, and ordinary exit codes; an independent raw-only oracle preserves the expected outcomes. This demonstrates narrow runtime portability only.
- **T:** Allocation `TEMPORAL-COALESCING-6315-WSLC-SUCCESSOR-20261002-01`; base main `c09f073f2a6e078c0fe5d8192246cc821cecc29c`; branch `research/wslc-temporal-coalescing-6337-t0-20261002`; result path `research/analysis/temporal_coalescing_6315_wslc_successor_20261002/`. One candidate invocation and, only after candidate exit 0, one separate auditor invocation; no retries. Pinned image digest, commands, outputs and hashes are in `FREEZE.json`, `RUN.md`, and `SHA256SUMS`.
- **D:** Candidate exit 0 and SHA-256 exactly equals the predecessor raw (`e8c3c30b38f5ab018c0caa272f31f3cdadc960331ba00c1adeb29cf9118f5812`). The independent audit reports 14/14 rows: 10 `PRESERVED`, 2 `NOT_PRESERVED`, and 2 `UNKNOWN`; all 4/4 mutations are rejected. Both `--rm` containers were absent from the post-run inventory. This meets the scoped portability gate.
- **C:** One Windows laptop; WSL package `3.0.1.0`; WSLc `3.0.1.0`; Ubuntu 24.04 WSL2; kernel `6.18.40.1-microsoft-standard-WSL2`; linux/amd64; cached Python digest `f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. The predecessor used linux/arm64, so architecture/runtime conditions differ. The kernel reported that cgroup/swap limit capability was unavailable. The requested 512 MiB is not evidence of an effective ceiling.
- **U:** Authored finite synthetic traces only. No live GUI or capture-coverage validation, continuous-time claim, real task effect, model/action authority, memory-pressure test, statistically valid performance comparison, broad Docker replacement, or product benefit.

## Measurements

The outer PowerShell stopwatch measured 2,548.89 ms for the single candidate `wslc run` and 538.4744 ms for the single auditor `wslc run`, including WSLc invocation/container lifecycle. These are one-shot elapsed times, not a speed comparison; there was no matched repeated native/Docker baseline. Peak RSS was not measured. WSL memory after the run showed 7.6 GiB total, 6.7 GiB available, and 0 GiB swap used, so this observation does not show host memory pressure.

Both commands surfaced: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The runs therefore confirm WSLc execution and input/output handling, but not a memory cap or memory-pressure relief.

## Construction history and evidence caveat

Before formal execution, the native WSL construction suite first found a defect in the new auditor test harness (mutation tuple unpacking); this was fixed before any candidate invocation, and the suite then passed 3/3. The failure is described in `CONSTRUCTION.md`; it was not a formal candidate/audit failure and did not consume either formal invocation.

PowerShell captured each WSLc launcher output with merged streams (`2>&1`), so the launcher transcripts are retained as observed; they are not represented as independently captured container stdout and stderr channels. The candidate source emits no stdout on success; the auditor's one status line is present in the combined transcript. The WSL/cgroup warning is emitted by the launcher/kernel path.

The read-only auditor source directory also contained a generated Python 3.12 `__pycache__` file left by a prior syntax compilation. The formal command directly invoked `auditor.py` with `python -B`; that cache was not executed. Its digest is recorded in `FREEZE.json`, but it is excluded from published source inputs.

The candidate read-only mount also contained `test_construction.py` from the preformal suite; the formal command directly invoked `candidate.py` and imported no test module.

The container inventory contained one pre-existing exited smoke-test container (`adadf5c4bd8d`, name prefix `ai-wsl301-migration…`). It was left untouched. After both runs, that same pre-existing row was the only listed container; the two named `--rm` containers were absent.
