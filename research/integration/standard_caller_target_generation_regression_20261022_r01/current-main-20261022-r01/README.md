# Current-main target-generation caller recheck

- Run ID: `AI-TARGET-GENERATION-CURRENT-MAIN-20261022-R01`
- Classification: local regression recheck; not a formal live experiment
- Source: `4bcf4e0a9254a8434032e00f6c4965e72c13293d`
- Host/runtime: Windows, CPython 3.11.9

## Result

The current-main public-caller lifecycle suite plus four compiled/owned-caller generation and fresh-session cases passed 20/20 in normal mode and 20/20 under `python -O`. The exact commands and named test output are retained in `normal.log` and `optimized.log`.

The suite includes same-process target destruction/reuse, destruction during initial capture, process-generation change during a compiled action, refusal of a stale alias, and recovery in a fresh session while preserving the previous cancellation receipt. The adversarial `DestroyNotify`-between-final-check-and-XTEST case also passes its *bounded* contract: one prefix press may already have occurred; the caller returns `execution_failed`, verifies prefix release, and refuses retry on the retired target. This is not atomic target-generation validation and does not prove no input can be emitted after the final local check.

## Scope and limits

This is a local Fake X/public-MCP caller regression recheck on the exact source SHA above. It is neither a new live experiment nor a repair of the target-lifecycle check/use race. It does not establish release under blocked live platform I/O, independent application task success, physical desktop or MAP01 control, WSLc portability, matched efficiency, or broad reliability. No WSLc or Docker allocation was used.

`SOURCE_BLOBS.txt` pins the relevant test and implementation files. This receipt supplements, and does not replace or modify, the historical R01 packet in the parent directory.
