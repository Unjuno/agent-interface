# Retrospective preservation: #6389 native-WSL2 pilot STOP

This is an archival custody note added on 2026-10-03, not a prospective freeze, a new allocation, or a new scientific result. The nine original files from [Draft PR #6434](https://github.com/Unjuno/agent-interface/pull/6434) at commit `414daf7150c671191049cdb0bfcb22b59fd82845` are retained byte-for-byte with their original Git modes. Their original subtree was `10cb580a3576426e1dd77450cc3d1df532733f2f`.

## Original outcome and execution boundary

The [original STOP](STOP.json) and [original freeze](FREEZE.json) retain allocation `ISSUE6389-NATIVE-WSL2-PILOT-T0-20261002-01`: `HOLD_RESOURCE_CONTENTION_AND_STOP_PYTHON_PATCH_VERSION_MISMATCH`.

- At 2026-10-02 01:54:34 UTC, native Ubuntu/WSL2 Python 3.12.3 differed from the cached WSLc Python 3.12.14 image. The 01:57:12 UTC contention snapshot found seven native workers plus a separate Xvfb/LibreOffice workload
- Native measurement-arm invocations = 0; WSLc measurement-arm invocations = 0; independent formal auditor invocations = 0. No timing/RSS comparison or migration-benefit result exists in this package
- Historical synthetic construction stdout records 10/10 native and 10/10 WSLc tests. These are not formal candidate results and predate the expected-Python hardening at the retained head; the resulting 11-test source was not executed in that historical review
- The original construction/preflight coordination deviation remains fully disclosed in STOP.json. This archive neither repeats nor legitimizes those invocations
- WSL software/WSLc version 3.0.1.0 is distinct from the WSL2 distribution version. Requested memory limits, low PSI, a successful smoke, or an exited container do not establish effective memory enforcement, lack of contention, or owner release

The [original README](README.md), [raw construction stdout](raw/), [auditor source](audit.py), [test source](test_audit.py), and [original SHA256SUMS](SHA256SUMS) are historical evidence. In particular, README's resume wording is a historical condition, not an execution instruction granted by this archive.

## Distinct later paths and corrections

1. The [artifact ownership addendum](https://github.com/Unjuno/agent-interface/issues/6389#issuecomment-5944357305) explicitly separates this 01:54/01:57 STOP from the later unpushed v2 preparation, standalone-runtime work, and bind-mount smoke. The v2 worktree/branch is not copied, modified, replaced, or claimed here
2. A [static source review](https://github.com/Unjuno/agent-interface/pull/6434#issuecomment-5944759559) found that the retained auditor reads `source_sha256` and `expected_test_ids` at the top level while the persisted freeze stores both under `workload`. Its synthetic tests use a flattened freeze. Keep this defect and the unexecuted hardening visible; successful repository checks did not validate this package's suite
3. [Merged PR #6618](https://github.com/Unjuno/agent-interface/pull/6618), commit `89f4fbd399f352c19f63ef543519b53fc4ed2025`, is the separate [auditor-contract repair](../native_wsl2_migration_6389_audit_repair_v1_20261002/REPORT.md). It retains the same FREEZE.json blob `4a3e9264982cc6235c5ec12af5a6aab1f7201f12`, but its repaired auditor/tests and new report are not the nine-file original archive. It is complementary, not a replacement for the original STOP, raw stdout, README, or source
4. The [later exact-interpreter correction](https://github.com/Unjuno/agent-interface/issues/6389#issuecomment-5946497597) and [subsequent gate recheck](https://github.com/Unjuno/agent-interface/pull/6434#issuecomment-5946823558) distinguish the cached CPython 3.12.14 executable/build from Ubuntu/container userland differences. They do not rewrite the earlier mismatch snapshot or establish shared-lane release
5. Later standalone, container, mount, and GPU smokes remain separate evidence at their own identities. In particular, the [out-of-allocation 03:05 smoke disclosure](https://github.com/Unjuno/agent-interface/pull/6434#issuecomment-5944896220) is not included in the frozen comparison or counted as a formal candidate/auditor invocation
6. The [latest checked migration continuation](https://github.com/Unjuno/agent-interface/issues/6389#issuecomment-5959586778), last updated 2026-10-02 19:10:27 UTC, records `HOLD_CLEAN_CHECKOUT_AND_WSLC_OWNERSHIP_GATE`. Clean current source, explicit lane ownership, source/input/runtime parity, independent raw-only audit, and applicable same-host cost gates remain unresolved prerequisites. #6693 is a separate Docker-vs-WSLc cost question; #6669's applicability/disposable-kernel-bounded-environment requirement is not released by this archive

No claim is made about the current user's computer. This preservation task used GitHub source reads and static byte/tree checks only.

## Custody and publication scope

[SOURCE_CUSTODY.json](SOURCE_CUSTODY.json) lists every original path, mode, Git blob, byte count and SHA-256, the source/base identities, and the unchanged original manifest's scope. The archive adds only this STOP.md and that custody manifest inside the original directory. The analysis index adds a short STOP pointer and the generated directory entry.

The original source PR/branch remains untouched. This Draft archive is not migration approval, host/resource release, rerun permission, a scientific PASS, or proof that every historical test was executed against the final source. Any main integration is a separate FINAL-v5 non-author content-review and conditional-apply decision; the archive preparer does not merge or write main.

## Static validation and limits

All nine original Git blob identities and modes match the source tree; all eight original SHA256SUMS entries match the retained bytes. The original manifest is unchanged and does not cover itself or these two retrospective metadata files.

Before publication, repository workflow review reused the unchanged `.github` tree `9feb96b8bb4e654c2df1c71cf190462678695399`, exact scoped-suite tree identities, and shared checker blobs from a prior static review. The archive changes no workflow or live runner. The eligible generic pull-request jobs are static navigation checks and explicitly scoped unrelated construction/regression checks, not discovery or execution of this #6389 package. The one-shot branch/create and formal PR guards do not match this archive branch. No source study, test, auditor, container, experiment, benchmark, or optional CI rerun was invoked by this archival task.

Workflow reachability review is not an observed check-pass claim. Third-party GitHub Apps, mutable upstream action tags/images, and out-of-repository automation remain outside this static repository-workflow review.

