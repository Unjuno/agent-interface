# Issue #6222 T0 preregistration

## Question and bounded claim

Does a crossed artifact × evaluator × setup × repeat audit expose planted verdict/ranking fragility that a one-pass decision plus a fixed positive/negative reference deck misses, while retaining stable-control rankings and refusing to treat shared agreement as truth? This is a finite synthetic method test only. It makes no claim about live agent benchmarks, any production oracle, physical gauge variance, or real-model performance.

## H / T / D / C / U

- **H:** The crossed audit detects the planted within-evaluator and setup-dependent ranking reversals; fixed standards remain stable; stable cases remain stable; shared-bias, ambiguity, UNKNOWN, and missing outcomes remain distinguishable.
- **T0:** A sealed 6-case, 24-artifact categorical fixture crossed over 2 evaluators × 2 setups × 3 repeats (288 candidate observations), plus a fixed positive/negative deck (24 reference observations). Cases cover deterministic stable controls, within-scorer flips, setup-specific flips, unanimous shared bias, semantic ambiguity, and differential missingness. The independent auditor reconstructs raw rows and summaries without importing candidate code, then rejects five prespecified corruptions.
- **D:** `PASS_METHOD_SCOPED` iff construction tests are green; exact frozen inputs/source/allocation/main hashes match; the fixed reference deck passes; stable remains exactly `A>B`; the within and setup cases each include `B>A` despite one-pass `A>B`; shared bias is flagged but not labeled a validity certificate; UNKNOWN remains distinct; missingness widens score intervals; the independent raw audit has no errors and rejects 5/5 mutations. Any failed gate is a preserved FAIL/STOP; no retry. A T0 pass does not validate any real scorer.
- **C:** A fixed standards deck and exact saved-state oracle may suffice in a narrow deterministic regime; apparent disagreement could be genuine ambiguity, changed artifact bytes, or missing evidence rather than scorer instability.
- **U:** The fixture is tiny and planted; evaluator correlation, order effects, mutable hidden state, and unrepresented boundary artifacts remain outside the test.

## Frozen inputs, ownership, and procedure

See [`FREEZE.json`](FREEZE.json) for allocation ID `CROSS-VERDICT-REPEATABILITY-6222-T0-HOST-20261002-01`, named local owner/task, exact source `main` SHA, branch, UTC window, source hashes, CPU-only execution boundary, one-candidate/one-auditor rule, and collision policy. Run locally on the Windows host using CPU only; no model/application, CUDA, GPU, Docker, WSL, or network during the run. The prior construction test is not a formal candidate or auditor invocation.

Immediately before execution, recheck that `main` still equals the frozen SHA, branch files byte-match local frozen files, source hashes and construction tests still match, and the output path is absent. If main advanced, the exact branch differs, any output exists, or a gate fails, stop and record HOLD/STOP without rebasing this allocation or retrying. Invoke the formal candidate exactly once. Only on exit code 0 invoke the independent auditor exactly once. Preserve stdout/stderr, exit codes, raw JSON, timestamps, and hashes. No source/input/result edits after the formal candidate starts.

## Host preparation snapshot

Observed before the window: C: free space 3,792,363,520 bytes; physical RAM 32,288 MiB total and 10,738 MiB free; CPU inventory query returned no usable processor row. Formal outputs are tiny. This assay uses neither the shared GPU nor Docker/WSL slots and does not claim or inherit their lease. Recheck local CPU availability and output path immediately before the run.
