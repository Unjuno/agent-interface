# Issue #5156 allocation-13: explicit-up owner/caller bracket in private Xvfb

Status: **STOP — candidate failed; auditor not run; no retry.** The one-shot candidate reached all explicit-up, stale-owner, and two teardown observations, then failed collecting cancellation cleanup by looking in a lease-local receipt list. The existing owner record confirms cleanup itself was logged; the lease-local instrumentation sink was the wrong retrieval path. This is a candidate/harness failure, not a passing formal result and not evidence that owner cancellation cleanup failed.

## H / T / D / C / U

**H.** For explicit caller-issued key-ups only, timestamps around the existing InputOwner v10 worker KeyRelease and XSync calls can join the transition-v3 explicit-up caller interval by occurrence, owner, intent and key without changing admission, release, request order or authority. Autonomous cancellation cleanup is a separate owner-only class, not forced into the explicit-up nesting predicate.

**T.** One disposable private Xvfb server in the cached linux/amd64 image:

1. Admit W and explicitly release W.
2. Admit W+A; attempt stale different-intent W-up (must reject, with no receipt and W still down); sequentially release owning W then A.
3. Admit W, set cancellation, attempt A (must reject), observe autonomous W cleanup to neutral.

Between scenario leases, call the existing owner `release` operation and require its `owner_release` receipt to be verified neutral, plus a neutral observer keymap, before a different intent is admitted. This is case teardown; it is not counted as a per-key explicit-up bracket. Candidate maximum=1; one separate raw-only auditor only after candidate exit 0; retries=0.

**D.** The three explicit-up occurrences must each be present once, match admission identity and satisfy `caller_start_ns <= owner_release_start_ns <= owner_sync_return_ns <= caller_return_ns`, with down-before/up-after keymaps. Stale W-up rejects without receipt and leaves W down. Cancellation rejects A and has one owner-only W cleanup row with ordered owner timestamps, matching admission/intent, down-before/up-after, reason=cancelled and a neutral owner record; no caller-nested claim is made. Both scenario teardown receipts are `owner_release`, verified with `keys_down=[]`, and keymaps show W/A neutral. Authority false and all owner/Xvfb processes clean. The independent auditor must accept pristine evidence and reject frozen identity/time/keymap/stale/cancel/teardown mutations.

**C.** Only a candidate-local copy timestamps existing KeyRelease requests and XSync returns. No additional X11 query is inserted between explicit per-key releases. Teardown uses the existing v10 release operation between cases. One ARM64-hosted amd64 image/Xvfb fixture; no distributional timing claim.

**U.** XSync brackets X server processing only, not exact hardware key-up or application delivery/usefulness. No physical desktop input, game/MAP01, model/provider, GPU, network, task-effect, safety/effectiveness, recovery, latency, human-tempo or transfer claim.

## Source/image freeze

Exact base/source Git blobs, LF-normalized vendored SHA-256, candidate/auditor SHA-256 and immutable image ID are in `FREEZE.json`. The four runtime dependencies are copied from exact current-main files. `serialize_release.py` is an additive local join helper copied byte-identically from unmerged A11 and is explicitly not claimed as current-main source. The v10 owner and v3 transition wrapper source remain otherwise unmodified in the vendored dependencies. The candidate builds a temporary instrumented copy under private container `/tmp`; source bind mount is read-only.

Image: `map01-attack-start-gate-4223-t8:20261001`, `sha256:d8c51b45569cc4fdf0f5d82ae285c3fbb20fae8525d6fab0cebadca171b3bebe`, linux/amd64. No image pull or build. Container is private, network-disabled, read-only root, requested 1 CPU/2GiB/128 PIDs and private tmpfs. The existing shared container is not inspected or modified.

## Construction checks

Construction is not formal evidence. Before candidate, run the frozen runner self-test and auditor positive plus corruption controls in the pinned image, verify all source/image/base/hash identities, empty unique output, exact container-name availability, and fresh main. Runtime enforcement of Docker resource settings is not inferred.

## One-shot candidate

Use a fresh empty result root; `formal-01` must not exist:

```sh
docker run --name unjuno-5156-xvfb-a13-candidate --rm --pull=never --platform linux/amd64 --network none --read-only --cpus=1 --memory=2g --pids-limit=128 --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m --mount type=bind,src=<PACKAGE>,dst=/src,readonly --mount type=bind,src=<EMPTY-RESULT-ROOT>,dst=/out --workdir /src --entrypoint python map01-attack-start-gate-4223-t8:20261001 -B /src/run_candidate.py --out /out/formal-01
```

Only on candidate exit 0, run exactly one independent auditor in a fresh network-disabled container with read-only source/result mounts and separate audit output. Nonzero candidate exit forbids the auditor and all retries for A13. Preserve exact raw/stdout/stderr/status without repairing the consumed allocation.

A12 partial raw and `STOP_CASE_SETUP_ACTIVE_PREVIOUS_LEASE` remain in its separate branch/PR; A13 does not reuse them.

## Formal outcome

- Candidate: **FAIL** (one execution; exit 1); independent auditor: **NOT RUN** (forbidden after candidate failure); retries: **0**.
- Failure: `RuntimeError: cancel cleanup did not produce exactly one release receipt` at candidate line 399. The runner searched `lease3._a13_owner_release_receipts`, but cancellation cleanup is performed asynchronously by the owner thread and the meaningful cleanup evidence is its owner record.
- Raw evidence: `raw.json`, SHA-256 `e9c70ea55924e428a52b9edbd8a7e16f7c61b30ecee11769407e56e5ee660daf`. It retains three explicit-up rows, stale-up rejection while W remained down, both neutral case teardowns, clean owner/Xvfb status, and the exact terminal exception. Since candidate_status is failed and cancellation evidence was not joined, this is not auditable as a full successful experiment.
- STOP reason: this allocation is consumed. A successor must separately test owner-record extraction, bind cleanup rows to the cancel admission identity, and add positive/corruption controls before a one-shot candidate.
