# Formal T0 run log — 2026-10-02

- Allocation: `ISSUE-6617-T0-WSLC-20261002-01`.
- Freeze: base `3246a9b6cb7a19209c4056d01472cb660390c4f4`; source hashes were rechecked immediately before the first formal invocation and matched `FREEZE.json`.
- Invocation order: one candidate, then one distinct raw-only auditor. Counts 1/1/0 (candidate/auditor/retries). No candidate or auditor retry.
- Candidate: exit 0; 10 scenarios × 3 arms = 30 traces.
- Auditor: exit 0; `PASS_METHOD_SCOPED`; errors=0; all four mutation controls rejected.
- SHA-256: raw `0edd1c334494d35b70e76ef54cb34afdbe08884c30bab4442a518151c9b044cd`; audit `206a6f82c5c2b5572bf5aa0a0d6374e8a8136b48e1d672222507046d0770698e`.
- Runtime: Microsoft WSL Containers `wslc.exe` 3.0.1.0, WSL kernel 6.18.40.1-1, pinned cached `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, Python 3.12.15, linux/amd64. `--pull never`, network none, source read-only, separate output mount. No image build, pull, or package installation.
- Both WSLc calls emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` One CPU/512M were requests only; no limit-enforcement claim.
- GPU not requested: the fixed event simulation has no GPU-dependent operation. Docker and Podman were not used.
- Construction checks before freeze: CPython 3.11.9; seven focused tests passed; `py_compile` and `git diff --check` passed.
- No STOP/FAIL occurred in the formal candidate or auditor. The resource warning is retained and does not change the disposition.

## Result

The version-bound read-only arm reaches its scripted stable-case verified effect in 3 logical ticks after the final committed request versus 6 for final-only preparation (3 stipulated ticks saved). Across revision, changed-recipient, quotation, speaker-switch and stale-completion cases, the raw-only auditor found zero provisional/unauthenticated/uncommitted admissions in either safe arm; the deliberately naive comparator made nine provisional admissions and they remained visibly unsafe. The accepted-but-effect-unknown case produced no allowed retry or blind inverse. A stop after verified irreversible effect was recorded as already occurred, not undone. Urgent held-input release was verified before the simulated planner completion.

The four mutation controls—old epoch, provisional prefix accepted as final, speaker merge, and cancellation treated as undo—were all rejected by the auditor.

This establishes only the frozen deterministic method behavior. It does not establish real speech recognition, authenticated speaker identity, what a person intended, safe voice control, GUI correctness, actual effect realization, human benefit, real latency, or product readiness. The one stable logical-time schedule is not a distribution or an empirical speed claim.
