# Issue #3349 - retained-event replay contract v1

Additive container contract matrix for stale-event replay defect documented in #3349.

Frozen main source path: research/doom/map01_recovery_cover_matched_v2_runner_3202.py
Git blob / required candidate SHA-256: 4432a6188b5318dc552f050a26ff9e2a5d32bbf9.
The local checkout is on another research branch and omits that path. Materialize candidate.py from the exact GitHub blob; Docker build verifies its bytes.

JsonSession.wait scans all retained events before reading the queue. The contract tests role/operation identity, stale accepted/rejected events, duplicate and wrong-ID terminal events, and a matching queued fallback response.

## H/T/D/C/U

- H: replay is safe only when wait role and operation identity match; terminal-cleanup replay works while stale prelude accepted/rejected rows cannot satisfy fallback-submit waits.
- T: matrix.py covers retained-terminal match, queued response, stale accepted/rejected prelude, duplicate terminal, wrong terminal ID, and unrelated retained event followed by queued response.
- D: all expected-policy cases must pass and the frozen candidate's stale-prelude witness must be independently reproduced. That witness reproduces the bug; it is not a product PASS. Accepting stale/wrong-ID rows or one of duplicate terminals is a failure. Missing engine/image/runtime is STOP.
- C: offline event/wait contract only; no MAP01, ViZDoom, X11, input, model, or formal allocation.
- U: no MAP01 recovery efficacy, scorer quality, live runtime safety, model utility, or formal allocation claim.

## Construction observations (host only)

The standalone policy oracle passed its finite cases after two initial expectation defects were caught and corrected. This is a local Python construction check only, not Docker evidence or a formal result.

## Container procedure

Network-disabled Docker run with pinned Python base, candidate source SHA gate, and isolated output. No host fallback is represented as Docker evidence.

    docker build --pull=false -t issue-3349-event-replay-v1 .
    docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=16m issue-3349-event-replay-v1

## Stop state

Source/test harness prepared. Formal container run is STOP_NOT_RUN_DOCKER_DESKTOP_DAEMON_UNAVAILABLE: desktop-linux returned no server metadata and the Docker CLI wait was interrupted. No Docker container was started.

No retries or formal MAP01 allocation are part of this contract harness.

