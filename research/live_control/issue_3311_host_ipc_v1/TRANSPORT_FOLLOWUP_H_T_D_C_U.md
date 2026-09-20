# #3311 v1 host-IPC transport follow-up

## H — hypothesis

The existing container-side v1 runner and host-side v1 broker can exchange one bounded, non-authoritative model request across OrbStack shared volumes when both sides use one declared `/repo` mapping and the IPC volume is shared. Before the fix, the one-shot broker reported exit 1 after a successful child exit 0 and omitted the frozen responder instructions from the Codex CLI request.

## T — bounded test

On OrbStack context `orbstack`, use local Linux/arm64 image `agent-interface-3311-runtime-v2:20260920` (`sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916`) with `--network none`. Mount a temporary fixture root at `/repo`, IPC at `/ipc`, and a temporary output root at `/out`. Start the existing v1 host broker with a fake Codex CLI and `--once`; execute the existing v1 container runner in handle/no-image mode. The fake CLI verifies that host-visible schema, responder instruction, and workspace files exist, then emits a synthetic thread/message/turn stream. Assert container and broker exit 0, exact request paths, `authority_granted=false`, invocation receipt, and returned event stream. Separately run the existing broker/backend/bridge contract suites.

## D — disposition

`PASS_V1_SHARED_VOLUME_TRANSPORT_ONLY`: the OrbStack round trip passed once; eight broker unit/contract tests and eight related bridge/runner/backend tests passed (16 contract/unit tests total). This does not establish real Codex CLI/model compatibility, a fresh schema-preflight PASS, GUI/task correctness, or any efficiency effect. Earlier v2 path-mapping STOP and #3311 dependency/preflight STOP records are unchanged.

## C — controls

Fake CLI only; unique temporary fixture paths; Linux/arm64 pinned image identity; `--network none`; no GUI app or task input; no authority-bearing request. The broker now refuses paths outside `/repo`, traversal and resolved symlink escapes, verifies schema/instruction/image SHA-256, requires non-authoritative mode/image consistency, forwards `model_instructions_file`, and returns the actual child exit code for `--once`. Its setup refusal is returned as a bounded broker STOP record instead of leaving the container waiting for the full timeout.

## U — unresolved / stop conditions

The current frozen schema preflight still uses a Windows-only CLI path. The next gate is to route a fresh no-image schema preflight through this same host-IPC boundary, record host CLI/runtime identity and usage, then validate the integrated desktop workflow in a separately frozen allocation. No conclusion about #3311's hypothesis is available until that new gate and independent task audit complete.

## Addendum — reviewed diagnostics and retained rerun (2026-09-20)

The original transport result above is retained unchanged. A review of the new broker code identified that missing IPC assets, which raise `OSError` subclasses, could be mislabeled as an unavailable host executable. The broker now distinguishes pre-invocation refusal, CLI identity timeout, and actual CLI spawn failure, and records whether a spawn was attempted. A regression test covers a missing schema and proves no CLI lookup/invocation occurs.

One additive OrbStack rerun was performed with the same pinned Linux/arm64 image and `--network none`; its unique raw bundle is `evidence/20260920-v1-transport-audit-01/`. The separately executed `audit_orbstack_v1_transport.py` reports `PASS_V1_SYNTHETIC_TRANSPORT_ONLY` across 13 checks, including exact image ID, one authority-false request, asset hashes, fake host CLI identity, event sequence, process boundary, zero exit codes and empty stderr. `raw-sha256.json` covers retained run files. The updated targeted suite has 18 passing tests (17 unit/contract tests plus this OrbStack transport test).

This remains synthetic transport-only evidence. No actual model call or compiled-schema endpoint validation was made; #3489's gate still requires #3487 merge and green latest-head CI before that one-shot test.

## Addendum — current-main regression and failure-stage taxonomy (2026-09-20)

After #3494 integrated the original v1 transport repair into main, the follow-up branch was merged with latest main without dropping #3494's `--once` exit-code regression. A further unit-only refinement now records request validation and distinguishes `HOST_BROKER_REQUEST_REFUSED`, `HOST_CLI_IDENTITY_UNAVAILABLE` / `HOST_CLI_IDENTITY_TIMEOUT`, and `HOST_BROKER_EXECUTABLE_UNAVAILABLE` at actual CLI spawn. Missing-schema and unavailable-identity regressions both assert that no model CLI spawn occurred.

The post-merge targeted suite passes all 20 broker, bridge, runner, backend, and OrbStack transport tests; `compileall` and `git diff --check` pass. The raw transport bundle above remains the preserved pre-merge OrbStack run; it is not rewritten to pretend the later taxonomy change was in that experiment. Hosted checks for the current PR head remain queued, and the real #3489 endpoint gate is still unrun.

### Spawn-failure semantics check

Added one more inert regression: when the validated request reaches the subprocess spawn boundary but the executable disappears, the broker records `HOST_BROKER_EXECUTABLE_UNAVAILABLE`, `host_cli_spawn_attempted=true`, and `host_cli_invoked=false`. Latest host suite: 21/21 passed including OrbStack round trip. Latest fixed-image OrbStack `--network none` unit run: 20/20 passed (the nested-Docker round trip is excluded there and separately retained above). These are contract/setup validations only; no model or task call occurred.

## Addendum — current-main reconciliation and retained rerun (2026-09-20)

Main then integrated the broader prompt/framing and broker failure-stage repair in #3498. That current-main implementation and its tests supersede the overlapping local taxonomy edits above; the branch adopts #3498 rather than duplicating it. The #3498-based targeted suite passes 22 tests including the real OrbStack fake-CLI transport test.

A fresh, separate OrbStack run against that current-main broker is retained at `evidence/20260920-v1-transport-audit-02/`. It uses the same exact Linux/arm64 image and `--network none`; the independent audit again reports `PASS_V1_SYNTHETIC_TRANSPORT_ONLY` across all 13 checks. The original #01 bundle and its audit remain untouched. Both runs are synthetic-only and do not satisfy #3489's real model/schema endpoint gate.

## Addendum — portable source audit and spawn receipts (2026-09-20)

Review found the first audit implementation compared historical absolute CLI paths and run source hashes to the present checkout. The raw #01/#02 bundles are unchanged. `source-revisions.json` now binds each bundle to the exact source commit; the auditor verifies those files with `git show`, compares the CLI path by executable basename plus recorded SHA/version, and emits re-audit output outside the immutable raw bundles. Both bundles pass 13/13 under the corrected auditor, including when #01 is copied to a different temporary checkout path.

Also adopted the current-main #3498 broker implementation unchanged, then made the spawn receipt consistent: `host_cli_spawn_attempted=true` once the subprocess boundary is entered, while `host_cli_invoked=false` on a spawn `OSError` and true on successful launch/timeout. Regression checks cover identity failure, spawn failure, timeout, and successful invocation. Latest host suite: 23/23; fixed-image OrbStack `--network none` unit suite: 22/22. No model call occurred.

## Addendum — immutable-manifest verification and broker cleanup (2026-09-20)

Codex review identified that the auditor could regenerate and overwrite `raw-sha256.json`, and that an image-inspect/setup exception could leave the `--once` broker alive. The auditor now reads the retained manifest and compares every captured raw file hash without writing into the bundle; audit reports remain explicit sidecar outputs. Both historical bundles still pass all semantic checks plus manifest verification. The transport test now places broker termination/reaping in `finally`, with kill escalation on reap timeout. A setup-failure regression confirms a broker process is reaped when image inspection fails.

Verification: host contract suite 22/22; fixed-image OrbStack `--network none` unit/contract suite 22/22; host OrbStack transport and setup-reap tests 2/2; historical bundle audits 14/14 each; `compileall` and `git diff --check` pass. These checks use synthetic/failure fixtures only; no model call occurred.

### CI and regression-test audit

A second test review found the prior setup-failure regression duplicated the cleanup sequence instead of invoking the transport harness's cleanup path, and no automated test proved a modified raw file is rejected without changing the frozen manifest. The cleanup sequence is now shared by the round-trip harness and setup-failure regression. New manifest tests cover intact, tampered, missing and malformed manifests and assert the baseline bytes remain unchanged. The Docker IPC contract workflow now runs these hermetic regressions and watches the auditor/test paths.

Verification: exact workflow test selection passes 19/19 on host; the OrbStack fake-CLI round trip separately passes 1/1; the pinned OrbStack `--network none` contract suite remains 22/22. Both historical bundles and a relocated copy each pass semantic and raw-integrity audit 14/14. `git diff --check` passes. No model/task/input call was made.

### Windows manifest-path normalization correction

Independent Windows re-audit found that host-native path rendering used backslashes for manifest keys, while the frozen JSON uses slash-separated relative paths. No raw evidence was changed. Manifest keys now use `Path.as_posix()`, the integrity regression uses a nested path, and the contract workflow includes a Windows-native Python job for the portable auditor tests.

The previous portability statement is superseded for the Windows host until the new workflow job completes. On this OrbStack/macOS host, the hermetic auditor and broker-reap suite passes 19/19 in the pinned no-network image; the synthetic OrbStack transport round trip passes 1/1. The two unchanged historical bundles and a relocated Linux copy each audit 14/14. This tests exact bundle integrity and semantics only, not host Codex/model behavior.

### Latest-main reconciliation (2026-09-20)

Before merge readiness, fetched main at `7cda063936b89c3f0cd58c0ebd1b78497e0ad2b8` and merged its two intervening commits (#3502/#3507). The five-file native-exchange/result update had no conflicts with this transport/audit scope and remains intact. On the immediately preceding code head, the Windows job and an independent Windows replay of both bundles passed; the mainline merge changes neither. Re-ran the host 19-case CI selection, synthetic OrbStack roundtrip 1/1, and fixed-image `--network none` contract suite 22/22 successfully; `git diff --check` passes. This branch is still a prerequisite-only transport/evidence change; no schema endpoint or task allocation was run.
