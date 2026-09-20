# Issue #3349 - retained-event replay contract v1

Additive container contract matrix for stale-event replay defect documented in #3349.

Frozen main source path: research/doom/map01_recovery_cover_matched_v2_runner_3202.py
Git blob ID: 4432a6188b5318dc552f050a26ff9e2a5d32bbf9. Raw source SHA-256: 4e700b05c60626e73070eb6f5883d9341c8b1374996d45f08e5766fc6cb0f463.
The local checkout is on another research branch and omits that path. Materialize candidate.py from the exact GitHub blob; Docker build verifies its bytes.

JsonSession.wait scans all retained events before reading the queue. The contract tests role/operation identity, stale accepted/rejected events, duplicate and wrong-ID terminal events, and a matching queued fallback response.

## H/T/D/C/U

- H: replay is safe only when wait role and operation identity match; terminal-cleanup replay works while stale prelude accepted/rejected rows cannot satisfy fallback-submit waits.
- T: matrix.py covers retained-terminal match, queued response, stale accepted/rejected prelude, duplicate terminal, wrong terminal ID, and unrelated retained event followed by queued response.
- D: the independent policy oracle must return only matching role/ID rows and fail closed on duplicate terminal history. Candidate audit must reproduce its declared stale wrong-ID early return and first-of-duplicate behavior. This is a false-rejection/wait-boundary defect, not evidence of unsafe input admission. Missing engine/image/runtime is STOP.
- C: offline event/wait contract only; no MAP01, ViZDoom, X11, input, model, or formal allocation.
- U: no MAP01 recovery efficacy, scorer quality, live runtime safety, model utility, or formal allocation claim.

## Construction observations (host only)

The standalone policy oracle passed its finite cases after two initial expectation defects were caught and corrected. This is a local Python construction check only, not Docker evidence or a formal result. An initial hash-labeling defect (Git blob ID compared to raw SHA-256) was caught before container execution and corrected; see the distinct identifiers above.

## Container procedure

Network-disabled Docker run with pinned Python base, candidate source SHA gate, and isolated output. No host fallback is represented as Docker evidence.

    docker build --pull=false -t issue-3349-event-replay-v1 .
    docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=16m issue-3349-event-replay-v1

## Stop state

Source/test harness prepared. Formal container run is STOP_NOT_RUN_DOCKER_DESKTOP_DAEMON_UNAVAILABLE: desktop-linux returned no server metadata and the Docker CLI wait was interrupted. No Docker container was started.

No retries or formal MAP01 allocation are part of this contract harness.

## Follow-up formal allocation (separate from the preserved 2026-09-20 STOP)

Issue #3349 is still open. A second OrbStack environment was available on
2026-09-20. Before formal execution, allocation `issue3349-event-replay-formal-01`
was frozen in `PREREG.json`; it pins the exact candidate/source hashes, current
main, seven per-case candidate and contract outcomes, Docker base image and
no-retry decision gates. The prior Docker-Desktop STOP above remains historical
evidence and is not overwritten or relabeled.

The frozen run uses a writable output mount only; source/root filesystems are
read-only, container networking is disabled, and no MAP01, game, X11, OS input,
model, or application is started. Formal evidence is written under `results/`
and independently recomputed in a second fresh container.

