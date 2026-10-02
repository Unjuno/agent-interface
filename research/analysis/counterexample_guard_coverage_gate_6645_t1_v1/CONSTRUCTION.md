# Construction and environment record

- Base: latest observed `origin/main` `adfb333264ed323a142170778f121a00b3970448`.
- Before formal start, parallel main advanced through six commits to
  `b573071d821e20e818304200a9e6ec8c9bbf5670`; changed paths were disjoint from
  this additive package except the shared analysis navigation index. The clean
  worktree was rebased to that exact main. Formal source hashes were unchanged;
  the base SHA and freeze time were refreshed before any candidate/auditor run.
- Runtime: OrbStack Docker Engine 29.4.0; CLI 29.5.2.
- Frozen local image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, Linux/arm64, `Python 3.12.14`.
- An engine/image-only container preflight passed with `--network none`, read-only root, 1 CPU, 512 MiB memory, 1 GiB memory+swap setting, 64 PID limit, all capabilities dropped, and no-new-privileges. This was not a candidate or auditor invocation.
- First construction test command failed 4/5: `test_known_harmful_state_is_refused_when_coverage_is_complete` raised `NameError: name 'contract' is not defined`; test setup also emitted two ResourceWarnings for unclosed JSON files. No formal candidate/auditor/container was started. The test code was corrected before source freeze.
- Corrected construction suite passed 5/5; Python compile and `bash -n` passed. Formal counts before freeze: candidate 0, auditor 0.

The Docker memory and swap settings are configuration only; this run does not
claim host/cgroup enforcement or memory-pressure validation.
