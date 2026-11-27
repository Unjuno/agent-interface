# Current-main recovered-caller task-oracle composition R01

**Disposition: `PASS_LOCAL_COMPOSITION_ONLY`.** On frozen main `cd708f52159cb87e38412640c49a59a0052c3e6d`, the focused existing `run_public_compiled` composition test passed 1/1 in normal Python and 1/1 under `-O` (CPython 3.11.9, Windows 10 build 26300).

## Finding

The synthetic recovered-dispatch path keeps graph completion separate from task truth. The caller yields `SAFE_YIELD / delivery_uncertain`, records zero completed graph transitions, denies replay, and accepts a valid independently returned task-oracle success. In the automatic-recovery subcase, the source action remains `UNKNOWN` with null task outcome and unconfirmed source release, while the distinct recovery receipt confirms release; task verification remains a separate valid result. A missing recovery key-up-attempt receipt fails closed: the caller returns `RUNTIME_FAILED`, does not call the task oracle, and leaves release unverified.

This answers a local composition question only. The callbacks and receipts are synthetic; this is not a public MCP/stdio end-to-end recovery, live GUI or task effect, recovery reliability estimate, MAP01 result, matched efficiency comparison, WSLc/Docker experiment, or Research Preview acceptance. No runtime behavior changed.

## Frozen inputs and raw output

`conditions.json` pins the main SHA, environment, exact test and source hashes. `raw/normal.log` and `raw/optimized.log` are the unmodified unittest command outputs. Both exit statuses were zero. `SHA256SUMS.txt` covers every packet file except itself.

## Next gate

Carry this distinction into a separately frozen public standard-caller recovery task with an independent task oracle and observable task effect, then repeat across fresh attempts. Do not infer public reliability from this synthetic pass.
