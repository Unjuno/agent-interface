# Native Win32 HWND reuse batch R02

This frozen no-input probe uses the production `Win32Backend` owner-identity
and `target_generation()` methods. On one Python process and GUI thread it
creates 256 hidden `STATIC` HWNDs, reads each identity and generation, destroys
all 256 and confirms each is no longer a window, then creates and reads a
second cohort of 256 before destroying them. At most 256 test windows exist at
once. Neither cohort is activated; no desktop capture or input is performed.

The result is `NO_HANDLE_REUSE_OBSERVED_IN_THIS_BATCH`: all 512 windows were
created and destroyed, the two cohorts shared no numeric HWND values, and the
10-check independent structural audit passes. The earlier R01 attempt stopped
before creating a window because its setup omitted `advapi32`; that failure is
preserved separately in the [R01 packet](../win32_hwnd_reuse_20261024_r01/README.md).

This is one finite allocation pattern on this Windows host and does not prove
that HWND reuse cannot occur, does not validate same-number reuse handling,
and does not establish atomic target fencing, input, release, recovery, task
effect, MAP01, WSLc portability, efficiency, or reliability. No production
code was changed based on this non-reuse result.

`conditions.json` was frozen before execution. `raw.json` contains every HWND,
owner identity, production generation digest, cleanup result and timestamp.
`audit.py` recomputes the discriminator from raw. `SHA256SUMS.txt` covers the
conditions, raw, probe, audit and report files.
