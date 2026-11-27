# R19 — temporary-volume comparison

## Frozen question and conditions

Does the same three-test recovery/caller group used in R18 remain stable when its per-mode temporary roots are placed under `D:\CodexData\Temp`? Source pins and test order are in `conditions.json`. The group ran once normally and once under `-O`; no retry was made. R18 used dedicated C: roots for the same group.

## Results

| TEMP volume | Mode | Tests | Duration | Outcome |
|---|---|---:|---:|---|
| C: worktree (R18) | Normal | 3 | 4.038 s | 3/3 pass |
| C: worktree (R18) | `-O` | 3 | 4.035 s | 3/3 pass |
| D: `CodexData\Temp` (R19) | Normal | 3 | 59.060 s | 1 failure, 2 errors |
| D: `CodexData\Temp` (R19) | `-O` | 3 | 168.923 s | 1 error |

Normal failed in the late-recovery/public-caller group and produced WinError 32 while cleaning `.report.json.tmp`; `-O` produced WinError 145 while removing a nonempty temp directory. The public-caller observer Future also timed out in normal. Exact logs and exit receipts are retained under `raw/`.

## Interpretation and limits

Changing the TEMP root is the only planned difference from R18. The contrast is strong evidence that the D: temp location or its storage/locking behavior is a material confound for these tests. It does not identify the lower-level cause (disk latency, filesystem filter, or another host-specific factor), and it does not turn R19 into a passing result. See R20 for the complete module on the C: temp path.

No live GUI, external input, model/provider call, task effect, reliability estimate, or efficiency result was produced.
