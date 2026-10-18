# Model economics convergence packet

Snapshot base: `1ece47014d05db898bf73afcd722a14524462e15` (2026-10-16). The later `origin/main` update observed on 2026-10-18 adds the saved V39 report package under `research/doom/v39_retained_pending_signal_trajectory_posthoc_a01_20261008/`; it does not change the source pins in this packet. This packet is a bounded local accounting-adoption comparison for #57/#3311, not a live-provider or application-effect experiment.

## Custody and replay boundaries

- `source-index.json` pins 11 source/data files by SHA-256. The matching files are under `sources/`.
- `original-proposals/index.json` records six unique original PR file blobs from #7521 and #8772. It preserves the model/test inputs while keeping distinct runner files separate.
- `saved-multiverse/index.json` records 11 preserved original evidence blobs. Original bytes remain untouched, including known manifest discrepancies.
- `idea-record-pin.json` binds the accompanying idea agenda snapshot. `probe-*.json`, stdout/stderr, and readback outputs preserve the normal and optimized local comparison. `exploratory/` keeps earlier failed/incomplete construction attempts as history.
- `read_saved.py` reads and audits preserved records; it is separate from the experiment driver. Do not rerun a consumed producer or reinterpret a saved local result as a new run.

## Bounded local comparison

Normal and optimized modes produced the same result:

| Model implementation | Test contract | Result |
|---|---|---|
| Current main | Current caller contract | 9 methods pass; 10 saved rows |
| Old #8772 model blob | Current caller contract | 2 expected failures: known turn ID is lost after await timeout and after completed-result publication failure; 10 saved rows |
| Old #8772 model blob | Old #8772 contract | 2 control methods pass |
| Current main | Old #8772 contract | 6 subtest errors from absent `thread_id` and changed malformed-usage failure-file expectations; these are not six failing test methods |

Each mode records four comparison cells and 20 raw rows; five negative mutants are rejected. This supports rejecting a wholesale old-module replacement under the current caller contract. It does not prove the older changes cannot be salvaged individually. In particular, adding `thread_id` only to an exception would not establish caller-side attribution unless the current consumer records it too.

## Preserved manifest discrepancy and limits

The saved original `RUN.json` is 1,917 bytes and has a trailing-LF difference from its pinned digest. Removing exactly one final LF yields the recorded original digest `66dadc1690c9954f4c5b39c32062db924fb7efb6f4c8d5f3ca0c64d78321b685`, but that normalization is diagnostic only: the preserved original remains byte-for-byte unchanged and its disposition is `HOLD_RUN_DIGEST_MISMATCH`. The saved raw audit is `PASS_METHOD_SCOPED` for five cohorts; it is not live robustness evidence.

No live provider, GUI, native input, application task effect, token spend, or matched performance comparison occurred in this packet. Do not claim efficiency, task success, or current live-control qualification from these local contract tests.

## PR disposition status

The agenda's proposed treatment is not an executed GitHub action. As checked on 2026-10-18, #7521 and #8772 were both draft/open at the recorded heads. Preserve the source blobs and evidence first; only then decide whether #7521 has no remaining independent work and whether #8772 contains a narrowly salvageable difference. This packet does not close either PR or establish owner/worktree custody.

## Integrity

`SHA256SUMS.txt` covers every regular file in this directory except itself. Verify from the repository root with:

```powershell
Get-Content research/integration/model_economics_convergence_20261016/SHA256SUMS.txt |
  ForEach-Object {
    $expected, $relative = $_ -split ':', 2
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path research/integration/model_economics_convergence_20261016 $relative)).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "SHA256 mismatch: $relative" }
  }
```
