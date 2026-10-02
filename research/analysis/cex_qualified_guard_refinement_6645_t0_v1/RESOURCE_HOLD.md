# Resource disposition — HOLD_RESOURCE

Formal WSLc candidate/auditor invocations: **0 / 0**. No formal allocation is
recorded for this package. The current machine is macOS and has no `wslc.exe` or
`wslc` executable. The empty inventory noted in another owner's #6354
preflight is an observation on that owner's host, not an assignment, release,
or permission for this task. Issue #5085 explicitly says unassigned work must
not self-assign or inherit a lane; its historical CPU request under #5927 is
also not this task's allocation.

No Docker, OrbStack, WSLc, GPU, network, GUI, model, user input, or external
application was used. The host candidate/auditor execution and unit suite below
are construction evidence only. Do not relabel them formal. Formal execution
requires a named host owner to confirm one bounded CPU-only WSLc allocation,
followed by a fresh check of main, branch/source hashes, image digest/platform,
output paths, and inventory. Without that exact grant the correct disposition
remains HOLD; no container is launched.

## Frozen one-shot boundary

- Candidate invocations maximum: 1.
- Separate auditor invocations maximum: 1, and only after candidate exit 0.
- Retries, tuning, seed replacement, or post-result repair: 0.
- Image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/amd64 (must verify on assigned host).
- Network, GPU, GUI, task input, and external effects: prohibited.
- Exact command forms: `RUN_COMMANDS.md` (plans only; not executed).
