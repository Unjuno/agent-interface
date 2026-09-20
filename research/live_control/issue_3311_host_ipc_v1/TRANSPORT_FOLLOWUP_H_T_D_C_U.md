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

### Review follow-up: immutable output and retained-bundle CI (2026-09-20)

**H** — The independent auditor must never write into an evidence bundle it is validating, and PR CI must audit the actual checked-in #01/#02 bundles rather than only synthetic temporary manifests. The checkout used for source-history verification must contain revisions named by `source-revisions.json`.

**T** — Reject `--output` anywhere under the evidence root and reject overwriting any existing retained path; allow a separate report path outside the root. Add direct audit assertions for both unchanged bundles and include `evidence/**` plus `source-revisions.json` in workflow path filters. Run auditor regressions on host and in the pinned OrbStack image with `--network none`; historical `git show` verification stays in host/CI checkout context.

**D** — Local PASS: 5/5 auditor tests pass on host, including full 14-check independent audits of both bundles; the pinned OrbStack no-network image passes the 4 tests that do not require Git or a historical object database; pinned-image bridge/broker/setup-reap selection passes 17/17. `git diff --check` is clean. CI on the new head is pending.

**C** — Bundles and frozen raw manifests were not modified. Explicit report output is refused inside the evidence tree (including existing raw paths) before writing; an external report path is allowed. The minimal runtime image has no Git, so container tests make no historical-source-provenance claim; full independent audits run in host/CI checkout context.

**U** — Latest-head Linux and Windows jobs have not completed; merge remains gated on required checks. No host Codex/model invocation or schema-preflight attempt was made.

### Current-main reconciliation after #3513/#3514 (2026-09-20)

Main advanced through #3513/#3514 while hosted Linux CI was queued. `git merge-tree` showed an automatic, conflict-free merge; the commits add lossless receipt references and compact public CLI review. The complete main update is merged into this branch without changing either frozen transport bundle.

**H/T** — Revalidate both the #3487 transport/audit contracts and the newly integrated public CLI receipt-review behavior after combining the histories.

**D** — PASS locally: host selection passes 31/31; the pinned OrbStack image with `--network none` passes 30/30. Host selection includes both retained evidence audits and their historical source `git show` checks. The container selection includes broker, bridge, auditor path-safety/manifest tests, cleanup regression and public CLI review tests; historical-source audits remain in the checkout environment because the runtime image intentionally has no Git. `git diff --check` is clean.

**C** — Main's receipt changes are independent of raw transport evidence; both raw bundles and frozen hashes remain untouched. No model, GUI, or task call occurred.

**U** — These tests are local and do not replace latest-head hosted CI. Main is now at `7d12e7afc1b1db163b74a54a821658c8c867e5c7`; push and wait for fresh required Linux/Windows results before merge. #3489 remains gated; no host Codex preflight was attempted.

### Review follow-up: bind Docker run image to inspected identity (2026-09-20)

**H** — A retained `docker image inspect` record is insufficient if the captured `docker run` command names a different image. The auditor must parse the image argument consumed by `docker run` and bind it to that exact inspect object's immutable ID/tag/digest; new runs should execute the inspected immutable image ID directly.

**T** — Add an independent `run_image_matches_inspect` check; construct a disposable copy of an unchanged retained bundle, change only its image argument, regenerate only the copy's manifest, and require audit failure despite the pinned inspect ID and a valid raw manifest. Change the OrbStack test harness to replace its tag placeholder with the inspected `Id`, save that exact command, and assert the recorded image argument equals the inspected ID. Never rewrite the historical #01/#02 bundles.

**D** — Host test selection passes 23/23, including both preserved-bundle audits, full rehashed-tamper rejection, and the live OrbStack fake-CLI roundtrip. Pinned OrbStack `--network none` Docker-independent selection passes 30/30. `git diff --check` is clean. The retained legacy bundles each continue to pass the strengthened cross-reference audit through their frozen tag in `RepoTags`/`RepoDigests`; future runs use the immutable image ID.

**C** — Raw #01/#02 bundle files and their original hashes remain untouched. The adversarial modified bundle exists only in a temporary directory and proves the image-binding check fails while the copy's regenerated raw manifest remains valid. No model, GUI, or task action occurred.

**U** — One exploratory attempt to run the nested OrbStack roundtrip test from inside the minimal runtime image failed because that image has no Docker CLI/daemon. This is an environment limitation, not an IPC/image-binding test failure; the real OrbStack roundtrip was run from the host and passed. Latest-head hosted CI/review still required; no #3489 call was made.

### Review follow-up: bound the image-inspect setup call (2026-09-20)

**H** — Image inspection must be bounded so a stalled Docker/OrbStack endpoint cannot prevent the transport harness's `finally` cleanup from reaping its one-shot broker.

**T** — Add a finite 15-second timeout to image inspection and simulate `TimeoutExpired` while a broker is live; require the original timeout to propagate and the broker to be terminal after cleanup. Include the regression in the Linux contract workflow and rerun OrbStack/network-isolated selections.

**D** — PASS locally: the complete host workflow-equivalent bridge/broker/audit/setup selection passes 24/24, including image-binding adversarial audit and the timed-out-inspect broker reap. OrbStack host roundtrip/setup selection passes 3/3; the pinned OrbStack `--network none` contract/review selection passes 31/31, including both broker reaping paths. `git diff --check` passes.

**C** — The timeout is bounded at the Docker client call; the pre-existing `finally` cleanup terminates then escalates to kill/reap. No retained historical evidence was modified; no model, GUI, or task was run.

**U** — Latest-head hosted Linux/Windows workflows and fresh review remain pending. #3489 remains gated on #3487 merge and green CI.

### Current-main reconciliation after #3517/#3519/#3520/#3522 (2026-09-20)

Main advanced four commits while hosted CI was queued. `git merge-tree` showed a clean automatic merge, including the overlapping host-CLI identity boundary from #3517; latest main was merged and its behavior retained. The new broker identity-probe timeout/nonzero regressions are now included in the combined suite.

**H/T** — Verify the transport/auditor/setup guards together with main's identity receipts, X11 partial-execution behavior, CLI review, and portable archive source pinning after reconciliation.

**D** — PASS locally: exact Linux workflow-equivalent selection 26/26 on host (including source-history audits); pinned OrbStack `--network none` broker/bridge, path-safe auditor tests, two setup cleanup cases, and public CLI review selection 33/33; OrbStack X11 partial-execution tests 4/4; host portable distribution tests 5/5. Historical source-audit tests run on host because the minimal image has no Git. `git diff --check` is clean.

**C** — All tests are deterministic or synthetic/failure-boundary tests; no real model, GUI task, or authority-bearing input ran. Raw #01/#02 bundles and manifests remain unchanged. The earlier attempted broad distribution suite inside the minimal image failed only because `git` is absent there; the host distribution suite and the correct Git-independent OrbStack selection passed.

**U** — Latest-head hosted CI must be rerun after this main sync and the branch pushed; review comments must be refreshed. #3489 is still gated, so no host Codex schema call was made.

### Review follow-up: correlate broker response and runner events (2026-09-20)

**H** — A retained transport PASS must demonstrate that the exact event stream returned over the shared-volume IPC response is the stream consumed and retained by the container runner; refreshing the raw manifest alone must not conceal a semantic mismatch.

**T** — Add an independent exact JSONL event comparison between `<request_id>.response.jsonl` and `out/runner/events.jsonl`, failing closed for a missing or malformed response. Add a host adversarial retained-bundle test that changes the broker response, regenerates only the temporary copy's manifest, and requires audit failure; add a Git-independent unit test for match, mismatch, malformed, and missing response cases. Re-audit both immutable retained bundles and regenerate their existing portable sidecar reports.

**D** — Both original OrbStack transport bundles pass the updated independent audit with response correlation and immutable raw-manifest checks. The deliberately modified temporary copy fails `runner_events_match_broker_response` even though its regenerated test manifest matches. The full host workflow-equivalent suite and the pinned OrbStack `--network none` Docker-independent suite are recorded in the PR validation update; no bundle bytes were changed.

**C** — Historical `evidence/**` and `raw-sha256.json` remain unchanged. The adversarial copy is temporary. Container validation uses the pinned Linux/arm64 image with `/repo` read-only and network disabled; source-history checks run in the host/CI checkout because the minimal runtime image intentionally has no Git. The evidence remains fake-CLI transport only.

**U** — This repairs the auditor's event-lineage gap; it does not exercise a real host Codex call or establish schema endpoint compatibility. Per #3489, that one-shot model preflight remains gated on #3487 merge and required latest-head CI green. #3311's formal cold/warm/invalidation/repair allocation remains separately unperformed.
