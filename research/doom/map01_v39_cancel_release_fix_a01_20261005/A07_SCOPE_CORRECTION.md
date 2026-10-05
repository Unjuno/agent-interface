# A07 scope correction — 2026-10-05

The three recorded ExecutorV12 expiry compositions override the base `execute()` and `release_all()` methods in their test harness. The harness uses a dummy release-backend base, so these runs do not exercise inherited current V39 coast/session `release_all()` and do not establish current V39 × ExecutorV3 inherited final-release behavior. The A07 result remains synthetic ExecutorV12/test-seam evidence.

The separate source-locked paired experiment in `../map01_v39_inherited_release_v3_a01_20261005/` tests the delayed owner-record boundary with the current coast/session class chain in the method-resolution order. In the candidate arm, a wrapper delegates to inherited `session_v5.Backend.release_all()` and drains records in `finally`; it emits one contextual receipt before terminal. This scoped fake-display result does not imply real X11, application, gameplay, or live-control success.

The A07 run and its source lock remain historical evidence against base main `bfd182727aebd9636c6a84fb437848c1dfe66be8`. Main later advanced to `dccf55e264f434ca27f2948fe53be09919047819`; the historical A07 auditor pins the former base and is not a current-main replay.
