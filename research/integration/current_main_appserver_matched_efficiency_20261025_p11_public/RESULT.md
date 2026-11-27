# P11 matched caller comparison — sanitized result

**Disposition: `PASS_SCOPED_MATCHED_FAKE_X_COMPARISON`.** Three counterbalanced pairs compared direct public input with the compiled public caller, for six one-shot cells on deterministic Fake X. A real App Server model turn selected a point from the exact public observation image in every cell. Each cell minted against that observation sequence, produced exactly one owner-side click/effect, changed the expected pixel, and verified release. A separate evidence scorer certified the synthetic task effect; runtime `task_success` remained `null` in all six cells.

The local frozen auditor recorded 15/15 checks for every cell, including source/runner identity, image provenance, effect and release evidence, and provider/ledger usage agreement. P10's separate pre-provider Python 3.11 setup failure remains excluded and unchanged. P09 remains separately preserved as incomplete due to raw-ledger mutation by its earlier redactor.

## Descriptive comparison

| Measure | Direct median | Compiled median | Paired median, direct minus compiled |
|---|---:|---:|---:|
| Provider turn (ms) | 5,926.8 | 5,167.7 | +759.1 |
| Observation to action return (ms) | 6,187.8 | 5,433.8 | +753.9 |
| Total trial (ms) | 6,959.3 | 6,071.2 | +888.1 |
| Input tokens | 10,197 | 10,203 | −6 |
| Output tokens | 60 | 58 | +2 |
| Reasoning output tokens | 41 | 39 | +2 |
| Public tool calls | 5 | 5 | 0 |
| Compiled transitions | 0 | 1 | — |

Both arms passed 3/3; each exact two-sided 95% Clopper–Pearson interval is 29.2%–100%. Pairwise latency differences point in both directions. Three pairs support descriptive medians only, not a causal speedup or reliability estimate. Image-input usage and upstream billing were unavailable.

## Scope and custody

The source runtime commit is `63cc6c4505745ddf4f4ac85baacb4828ca572d49`, an ancestor of current main `75d55fabec81791de4ff899c9d7478f8ff1ad02e`. The 10 preregistered runtime source hashes and six runner hashes were independently rechecked against current main and the local packet; all matched. The original local packet manifest contains 522 entries, all of which were independently hash-verified.

The full raw packet is retained locally and is not included here: immutable provider/MCP `.bin` files contain a local Windows profile path. This sanitized derivative includes the frozen conditions, preregistration and bounded result summary; it does not provide the raw records needed to replay the audit independently. No raw data, original outcome, or audit file was modified to produce this derivative.

This is synthetic Fake X provider-to-standard-public-MCP evidence. It does not establish physical input, live application or MAP01 transfer, WSLc behavior, blocked-I/O release/recovery, efficiency outside this task, or broad reliability. No WSLc or Docker allocation was used.
