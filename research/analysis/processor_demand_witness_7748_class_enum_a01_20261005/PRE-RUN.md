# Issue #8061 pre-run receipt

- Allocation: `7748-CLASS-ENUM-A01-20261005-01`
- Authorization: successor Issue #8061 was created at 2026-10-05T06:56:47Z, before formal candidate/auditor execution.
- Base `main`: `3239217f54c199b582924ee69c7c80402f418a63` (merge of PR #8054).
- Target additive path: `research/analysis/processor_demand_witness_7748_class_enum_a01_20261005/`; absent from frozen main before this work.
- Branch: `research/7748-class-enum-a01-20261005`; exact-name branch search and remote-ref check found no collision.
- Related ownership: #7748 is historical and PR #7762 is merged. Open #7778 mentions the unknown-class auditor caveat. Targeted Issue/PR/branch searches for `7748`, `unknown job class`, `7748-class`, and `job-class` found no successor allocation or competing branch for this class-enum test.
- Predecessor hashes and result are frozen as read-only identities in `FREEZE.json`; no predecessor candidate or auditor CLI was run.
- Construction command: recorded in `CONSTRUCTION.log`; 6 tests passed before freeze.
- OrbStack preflight: the previously allocated private VM `obs-5905-a04-20261005` contains the pinned Python image. One no-network container canary failed before Python startup with `crun: bpf create: Operation not permitted: OCI permission denied`. No candidate or auditor executed in a container; no image/daemon mutation was attempted. `ENVIRONMENT.json` preserves the exact image and VM identities.
- The Issue explicitly permits a host-only run for this standard-library deterministic model after container failure, with no isolation/resource-enforcement claim. Host runtime: CPython 3.14.5, macOS 27.0.1 arm64.
- Formal candidate invocations before freeze: 0. Formal raw-only auditor invocations before freeze: 0. Formal retries: 0.
- Candidate formal output path: `results/candidate.raw.json`. Independent audit output path: `results/AUDIT.json`. Neither existed before the frozen calls.
