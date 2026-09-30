# Issue #3270 Docker Desktop replay and construction revalidation (2026-09-30)

## H / T / D / C / U

- **H:** The immutable #3270 scorer-jitter replay test still reproduces its retained one-overdue-period accounting in a local Docker Desktop container, and the separately frozen recovery-v2 preregistration still passes construction validation.
- **T:** Re-fetch the exact replay test, preregistration, and validator from GitHub `main`; verify their SHA-256 values; run both checks inside the existing local Python container image with networking disabled, source mounted read-only, and image pulls disabled. Do not invoke ViZDoom, the formal recovery runner, a model, or a GPU.
- **D:** **PASS — replay reproduction (2/2 unit tests) and construction validation.** Exact commands and output are below.
- **C:** This is a local deterministic replay/construction revalidation only. It does not resolve #3259 allocation -07's formal `FAIL`, measure recovery efficacy, or authorize/consume a fresh MAP01 allocation. Earlier #3270/CI evidence remains unchanged.
- **U:** The remaining fresh formal MAP01 allocation requires its own current-main source freeze, exact owner-confirmed shared-resource lease, collision check, and independent audit. The latest inspected coordination record (#5085) did not grant this lane a lease; this revalidation therefore stopped before live execution.

## Provenance and environment

- GitHub repository: `Unjuno/agent-interface`
- Source ref inspected after the local run: `main` at `2e07f7b6806020cf57bd8d8d86a672d18f266fca`
- GitHub main file-content SHA-256:
  - `research/doom/test_map01_scorer_scheduler_replay_3270.py`: `DEC6E6D8E929BEE06CDBCE6D1E2179F030DFC5574C01054C4FC236DC5223F4FB`
  - `research/doom/map01_recovery_cover_matched_v2_prereg.json`: `4420A1A40FE32BB447DDAACA505CD6A232D06231AA413F71C6AF52B12E066E40`
  - `research/doom/validate_map01_recovery_cover_matched_v2.py`: `2414FDE828749AE8A455052948299F613FC4E28D43905D871AF7F3897D060783`
- Docker Desktop: engine 28.5.1, context `desktop-linux`, Linux/x86_64.
- Image: `python:3.12-slim`, local image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, RepoDigest `python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Inputs were fetched from GitHub into fresh temporary host directories. Each container used `--network none`, `--pull never`, and a read-only bind mount. No repository checkout was modified.

## Replay reproduction

Command (with the fetched replay test mounted read-only as `/replay.py`):

```sh
docker run --rm --network none --pull never \
  --mount type=bind,source=<temporary replay.py>,target=/replay.py,readonly \
  python:3.12-slim python /replay.py -v
```

Output:

```text
test_observed_single_overdue_period_is_local_and_non-catchup ... ok
test_replay_preserves_sample_cardinality ... ok

Ran 2 tests
OK
```

The observed replay disposition remains `[0, 0, 1, 0, 0]`; no catch-up sample is fabricated.

## Frozen construction validation

The preregistration retains status `FROZEN_CONSTRUCTION_ONLY_NO_LIVE_LEASE` and allocation ID `map01-recovery-cover-matched-live-v2-01`.

Command (the preregistration and validator were mounted read-only at `/workspace`):

```sh
docker run --rm --network none --pull never \
  --mount type=bind,source=<temporary input directory>,target=/workspace,readonly \
  --workdir /workspace python:3.12-slim \
  python validate_map01_recovery_cover_matched_v2.py \
    map01_recovery_cover_matched_v2_prereg.json
```

Output:

```json
{"allocation_id": "map01-recovery-cover-matched-live-v2-01", "decision": "PASS construction validation", "formal_live_authority": false, "schema": "map01-recovery-cover-matched-v2-prereg"}
```

## Scope and preservation

This additive receipt does not modify `SCORER_JITTER_REPLAY_3270.md`, its CI addendum, any raw allocation artifact, the frozen preregistration, or allocation -07's result. No live allocation, ViZDoom process, model/GPU call, or shared runtime/workflow edit occurred.
