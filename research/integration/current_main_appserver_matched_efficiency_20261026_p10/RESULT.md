# P10 result — matched App Server caller routes

**Classification: `PASS_SCOPED_ALL_EFFECTS`.** Six preregistered one-shot trials ran on current-main runtime `b62eed22eda49c7f76813930492c53326fd45391`, with model `gpt-6.1-sol` at low effort. All six were model-grounded Fake X runs. No WSLc, Docker, physical input, live desktop application, or MAP01 was used.

## Per-cell observations

Times are milliseconds. Token columns are App Server reported input/output/reasoning counts. Direct-minus-compiled deltas are calculated within each pair.

| Pair | Arm | Input | Output | Reasoning | Provider turn | Observation to action return | Total trial | Independent effect + release |
|---|---|---:|---:|---:|---:|---:|---:|---|
| p01 | Direct public input | 10,093 | 57 | 38 | 5,657.76 | 5,910.15 | 6,668.26 | Pass |
| p01 | Compiled public caller | 10,099 | 55 | 36 | 5,001.85 | 5,274.83 | 5,918.37 | Pass |
| p02 | Direct public input | 10,093 | 59 | 40 | 5,730.91 | 5,988.36 | 6,764.89 | Pass |
| p02 | Compiled public caller | 10,099 | 59 | 40 | 5,963.42 | 6,253.94 | 6,901.13 | Pass |
| p03 | Direct public input | 10,093 | 54 | 35 | 5,749.37 | 5,996.48 | 6,772.14 | Pass |
| p03 | Compiled public caller | 10,099 | 55 | 36 | 5,946.35 | 6,232.34 | 6,885.28 | Pass |

Each cell selected a point inside the green target, matched the exact owner click, produced exactly one click effect and the expected independent final pixel, completed its selected action route, and verified neutral input release. The public observation image hash equaled the model-input image hash in all six cells. The compiled arm used one compiled transition; the direct arm used none.

## Paired deltas

Direct minus compiled:

| Pair | Input tokens | Output tokens | Reasoning tokens | Provider turn | Observation to action return | Total trial |
|---|---:|---:|---:|---:|---:|---:|
| p01 | -6 | +2 | +2 | +655.91 ms | +635.32 ms | +749.89 ms |
| p02 | -6 | 0 | 0 | -232.51 ms | -265.59 ms | -136.25 ms |
| p03 | -6 | -1 | -1 | -196.98 ms | -235.86 ms | -113.14 ms |
| **Median** | **-6** | **0** | **0** | **-196.98 ms** | **-235.86 ms** | **-113.14 ms** |

The direction of the timing difference changed in p01; the median favors direct input by about 197 ms of provider-turn time and 113 ms of total trial time in this three-pair sample. This is descriptive evidence only. It does not establish a general speed or reliability advantage.

P03's direct arm reported 8,192 cached input tokens; the other five cells reported zero. The frozen primary token comparison uses App Server input, output, and reasoning counts; cached-input detail is retained per cell in `RESULT.json`/the exported ledger. No pricing or upstream account-billing conclusion is made.

## Independent audit and custody

The private audit reports 6/6 effect-and-release passes, 6/6 complete ledgers, 6/6 raw attempt-recorder reconciliations, and 6/6 private raw-manifest checks. For every cell, normalized usage agrees across the App Server terminal result, terminal trial result, protocol journal, and reconciled attempt ledger. The public export has 408 files, 279 recorded privacy redactions, and 54 withheld private raw/binary files indexed by relative path, byte count, and SHA-256. A post-export scan found no unredacted Windows absolute paths or sensitive-field values, and all public file hashes matched.

Private raw originals remain local-only and were not changed by the exporter. The public packet permits hash comparison but does not expose raw attempt bytes, so a public reviewer cannot independently re-run private raw-ledger reconciliation. App Server usage is reconciled to its protocol journal and attempt ledger; independent upstream billing/account-level usage is unavailable.

With 3/3 successes per arm, the two-sided 95% exact-binomial interval for each arm's success probability is approximately 29.2%–100%. The study is too small to support a broad reliability estimate.

## Scope boundary

This closes only the scoped synthetic Fake X matched-caller comparison. It does not establish live application control, GZDoom/MAP01, WSLc, blocked-I/O release/recovery, cross-domain transfer, or broad reliability. The parent computer-control goal remains active.
