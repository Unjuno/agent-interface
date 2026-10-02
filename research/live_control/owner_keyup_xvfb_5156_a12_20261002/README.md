# Issue #5156 allocation-12: explicit-up owner/caller bracket in private Xvfb

Status at freeze: candidate and independent audit not yet run. This README records the preregistered question and repeatable local procedure; it is not a result. A10's bootstrap STOP and the inconsistent, unlaunched A11 package remain unchanged.

## H / T / D / C / U

**H.** For explicit caller-issued key-up operations only, timestamps around the current InputOwner v10 worker's existing XTest KeyRelease and XSync calls can join the transition-v3 wrapper's caller bracket by occurrence, owner, intent and key without changing admission, release, request ordering or authority. Autonomous cancellation cleanup has no explicit-up caller bracket and is a separate receipt class.

**T.** One disposable, private Xvfb server in the cached linux/amd64 image. Cases:

1. Admit W and explicitly release W.
2. Admit W and A; try W-up from a stale different intent (must reject and preserve the owning hold); then release W and A sequentially.
3. Admit W, request cancellation, and attempt A admission; cancellation cleanup releases W and the A admission must be rejected. Record that cleanup as owner-only autonomous release, not as an explicit-up nested bracket.

Candidate maximum=1. A separately implemented raw-only auditor runs at most once and only if candidate exit=0. Retries=0. No game/MAP01/model/provider, physical desktop input, shared container, GPU, WSLc, or network.

**D.** PASS only if the three explicit-up occurrences are each joined exactly once to the matching admission and satisfy `caller_start_ns <= owner_release_start_ns <= owner_sync_return_ns <= caller_return_ns`, with keymap down-before/up-after. The stale other-intent W-up must reject without a release receipt and leave W down. Cancellation must reject A and independently record one owner-only W cleanup receipt (`reason=cancelled`, owner interval ordered, down-before/up-after, matching admission/intent, neutral owner record); no explicit-up nesting claim is made for that autonomous cleanup. Authority remains false and all processes exit cleanly. Source/image/base must match FREEZE.json. Any mismatch is retained as FAIL/STOP, not repaired in-place.

**C.** The server-processing bracket ends when the XSync call returns. This one ARM64-hosted amd64 image/Xvfb fixture does not estimate a timing distribution. Existing owner-loop focus validation may run as part of unchanged v10 behavior; the instrumentation adds no X11 query.

**U.** No physical key state, application delivery/usefulness, MAP01 occupancy/effect, efficacy, safety rate, recovery quality, human tempo, latency, or transfer claim.

## Source and image freeze

See `FREEZE.json` for exact source Git blob IDs, locally vendored LF-normalized SHA-256, candidate/auditor hashes, and immutable image ID. The source blobs are copied as text with CRLF normalized to LF; their upstream Git blob identities are recorded separately, and the exact local bytes used are independently hashed. The X11 input owner and wrapper implementations are otherwise unmodified in the vendored source. The candidate generates a temporary instrumented owner in `/tmp`; the bind-mounted source is read-only.

Image identity: `map01-attack-start-gate-4223-t8:20261001`, `sha256:d8c51b45569cc4fdf0f5d82ae285c3fbb20fae8525d6fab0cebadca171b3bebe`, linux/amd64. Present in OrbStack with Python/PyXlib/XTEST/Xvfb. The host is ARM64, so Docker uses amd64 emulation. No pull or build. The one-shot candidate container is private/dedicated and will not inspect or modify the existing shared container.

## Pre-candidate checks already executed

- Candidate instrumentation construction: PASS; exact release/edit anchors found; patched module compiles; query counts for `query_keymap`, `get_input_focus`, and `input_state` remain identical to v10; release-join positive/control checks pass.
- Independent auditor self-test: constructed before candidate; must accept a positive synthetic raw and reject explicit-up/cancellation/source/identity mutations. This is a construction gate, not candidate evidence.
- Container: network disabled, read-only root, 1 CPU/2 GiB requested, 128 PID limit requested, private 64 MiB `/tmp`, read-only source mount, unique writable result mount.
- These are construction checks, not the candidate result. Runtime enforcement of configured Docker limits is not inferred.

## Candidate command

Replace the host source path with this package's absolute path and choose a new empty host result directory. The formal output subdirectory must not already exist.

```sh
docker run --name unjuno-5156-xvfb-a12-candidate --rm --pull=never --platform linux/amd64 --network none --read-only --cpus=1 --memory=2g --pids-limit=128 --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m --mount type=bind,src=<PACKAGE>,dst=/src,readonly --mount type=bind,src=<EMPTY-RESULT-ROOT>,dst=/out --workdir /src --entrypoint python map01-attack-start-gate-4223-t8:20261001 -B /src/run_candidate.py --out /out/formal-01
```

Only after candidate exit 0, run the separate auditor in a fresh network-disabled container with the source and result mounted read-only, and a distinct writable audit output path:

```sh
docker run --rm --pull=never --platform linux/amd64 --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,noexec,size=32m --mount type=bind,src=<PACKAGE>,dst=/src,readonly --mount type=bind,src=<RESULT-ROOT>,dst=/result,readonly --mount type=bind,src=<AUDIT-ROOT>,dst=/audit --workdir /src --entrypoint python map01-attack-start-gate-4223-t8:20261001 -B /src/audit_raw.py /result/formal-01/raw.json --out /audit/AUDIT.json
```

The exact outputs, stdout/stderr, exit statuses, raw SHA-256 and audit receipt are retained next to this README after the one-shot run. A candidate nonzero exit forbids the auditor and any retry under allocation-12.

Allocation-10's bootstrap STOP is in the adjacent `owner_keyup_xvfb_5156_a10_20261002/STOP.json`; it is preserved and not reused.
