# Portable runtime current-main recheck R01

Status: PASS_PACKAGING_AND_BASIC_STARTUP_CONTRACTS.

The complete `runtime/distribution_v2/test_*.py` suite ran against exact main `d5ada452527f97b90c3265966a6aebd7743cf483` using existing interpreters and no dependency installation:

| Environment | Mode | Result |
|---|---|---:|
| Windows CPython 3.11.9 | normal | 21/21 PASS |
| Windows CPython 3.11.9 | `-O` | 21/21 PASS |
| Ubuntu WSL CPython 3.12.3 | normal | 21/21 PASS |
| Ubuntu WSL CPython 3.12.3 | `-O` | 21/21 PASS |

The suite covers deterministic zipapp construction, committed-source pinning, archive contents, validation outside a checkout and side-effect-disabled doctor behavior. Exact commands, stdout/stderr and exit receipts are retained here; `SHA256SUMS.txt` covers every packet file except itself.

This verifies the portable archive’s construction and basic CLI contract on Windows and Ubuntu WSL. It does not establish native GUI input, permission flow, live task effects, provider behavior, macOS support, a published runtime release, or full Research Preview acceptance. No live allocation, model call, GUI action, input, container, package install or network download occurred.
