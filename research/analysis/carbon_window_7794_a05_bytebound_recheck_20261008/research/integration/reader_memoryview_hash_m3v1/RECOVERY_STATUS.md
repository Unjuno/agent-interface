# Recovery status for #4451 formal allocation

The frozen 11-file source/gate package is preserved unchanged. The Issue
records exact source readback and authorizes one allocation, but formal count
remains zero.

## Formal gate

No formal run was started during recovery. The frozen environment is Linux
x86_64 with CPython 3.13.5. The cached local `python:3.13.5-slim` image is
Linux/arm64; cached X11/Linux-amd64 images use Python 3.12.14. Neither matches
the frozen measurement platform for this `tracemalloc`/performance comparison.
No cross-platform formal result is substituted.

The frozen preflight also records runner-level interruption risk: resource
workers are serial, each has an 8-second limit, and `RAW.json` is written only
after the worker loop. Formal resource rows and the formal auditor were not
invoked during recovery.

## Construction-only check performed during recovery

The unchanged frozen runner was executed with `--phase construction` in cached
CPython 3.13.5 Linux/arm64, network disabled and source mounted read-only. Its
separate 64-record construction corpus produced 6 resource rows and 2 contract
rows, all with exit code 0. The captured raw receipt is
`recovery_construction_arm64/RAW.json` (SHA-256
`39415b1c5cf5181d490a290784b26e9203b16871e2b81eb9e298efdd942466e4`). This is
platform-specific construction evidence only; it is not any of the 24 formal
resource rows and does not validate the x86_64 timing gate.

The original construction `run02` audit PASS / 10-of-10 controls and prior
`FAIL_RESOURCE_COUNT_HARNESS` remain preserved in the freeze as separate
historical construction records.

Disposition: `HOLD_NOT_RUN_PLATFORM_MISMATCH`. This is not a scientific FAIL and
does not close #4451. Do not alter the frozen runner or use construction rows as
formal evidence. A future formal execution must use the frozen platform and
retain all 24 resource rows, both contract blocks, raw audit and effective
corruption controls.
