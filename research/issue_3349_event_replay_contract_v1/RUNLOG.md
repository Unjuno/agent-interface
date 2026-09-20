# Issue #3349 formal container run

## H/T/D/C/U

- **H:** `JsonSession.wait` scans all retained events before reading the queue,
  so event-type matches from an earlier operation may be returned before the
  caller checks the operation ID. Duplicate terminal rows may be silently
  resolved to the first row.
- **T:** Execute the exact frozen `JsonSession.wait` AST method on the seven
  preregistered event histories and independently recompute contract/candidate
  dispositions in a second container.
- **D:** The hypothesis is reproduced: old accepted/rejected prelude and wrong
  terminal IDs return; duplicate terminal history returns its first row. The
  role/ID-bound oracle passes 7/7; a fresh second-container verifier agrees on
  all seven.
- **C:** Synthetic offline wait-contract only. No MAP01 run, game, GUI, OS
  input, model, live runtime, or application was started. The test does not
  imply unsafe input admission.
- **U:** No recovery efficacy, live runtime safety, scorer quality, model
  utility, or formal allocation claim.

## Freeze and runtime

- Allocation: `issue3349-event-replay-formal-01`.
- Preregistration: commit `19525a8b1`; image IDs were pinned in commit
  `50e2a7887`, both pushed before formal execution.
- Main source: `a08935cc6efb73322e247b519fbd9d63a7b2741f`.
- Exact candidate blob: `4432a6188b5318dc552f050a26ff9e2a5d32bbf9`;
  raw SHA-256 `4e700b05c60626e73070eb6f5883d9341c8b1374996d45f08e5766fc6cb0f463`.
- OrbStack Docker Engine `29.4.0`, Linux/arm64 (daemon reported `linux/aarch64`).
- Base image:
  `python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db`.
- Formal image:
  `sha256:d2354e9963c3c4b78250810cbd1fe81af0e1b9e0f95a160dd60cd80355f34aad`.
- Independent image:
  `sha256:ca9a595beddbf56d00794297baf4b1ab3992f7d2b5795618c81892ac7417a383`.
- One formal invocation; one independent verifier invocation; no retries or
  replacement allocations. Build/preflight was separate and completed before
  the formal invocation.
- Runtime network disabled; root filesystem read-only; bounded `/tmp` tmpfs;
  formal output on its own writable mount. The second container mounted formal
  output read-only and wrote only to the separate independent-output mount.

## Commands

Run from the repository root, using the pinned local image IDs from
`PREREG.json`:

```sh
docker --context orbstack run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=16m \
  -v "$PWD/research/issue_3349_event_replay_contract_v1/results/formal-01:/out:rw" \
  sha256:d2354e9963c3c4b78250810cbd1fe81af0e1b9e0f95a160dd60cd80355f34aad \
  --output /out/RESULT.json

docker --context orbstack run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=16m \
  -v "$PWD/research/issue_3349_event_replay_contract_v1/results/formal-01:/evidence:ro" \
  -v "$PWD/research/issue_3349_event_replay_contract_v1/results/independent-01:/out:rw" \
  sha256:ca9a595beddbf56d00794297baf4b1ab3992f7d2b5795618c81892ac7417a383 \
  --result /evidence/RESULT.json --output /out/INDEPENDENT.json
```

Both commands exited 0. Each container used `--rm`. After both completed,
`docker ps -a` filtered by each image ID returned no rows.

## Results

Formal receipt: `results/formal-01/RESULT.json`.
Independent receipt: `results/independent-01/INDEPENDENT.json`.
The independent receipt binds the exact formal-receipt SHA-256 and independently
extracts/executes the frozen wait method while recomputing each contract policy.
All frozen file hashes and result hashes are listed in `SHA256SUMS`.

The older Docker-Desktop daemon-unavailable STOP remains preserved verbatim in
`README.md` as a distinct earlier environment/time. It was not overwritten or
reclassified; this later allocation used the available OrbStack engine.
