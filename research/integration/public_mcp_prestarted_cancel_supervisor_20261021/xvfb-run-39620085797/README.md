# Isolated prestarted-supervisor Xvfb run 39620085797

## Frozen execution

- GitHub Actions run 39620085797, job `prestarted-cancel-xvfb`, PR #9315.
- PR head commit `422f7ea68b225b85e5fcc05e37b9faf874716e26`; raw `GITHUB_SHA` is `25ed05af72a0baa8202427fed51699bc6e61b068` (the pull-request merge ref).
- Ubuntu 26.04, Python 3.12.15, Xvfb 2:21.1.22-1ubuntu1.3. Raw JSON, observation image and empty server log are copied byte-for-byte.
- SHA-256: raw JSON `63a49a3836052828a2d1d2a8181f6623fe840c3ed37fd0e9c2fa1b01af9e30f8`; observation PNG `751e00d5f926a15128a45baec1b2310aabee740b363119bd79dd224986d81f01`; Xvfb log `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

## Outcome and relation to prior run

The public MCP call reached the owner and the supervisor, but returned the same `invalid_cleanup_request` result as run 39618514760. It retired the owner (exit `-15`) in 16.579 ms, while independent release readback and task oracle remained absent; runtime cleanup stayed UNKNOWN, release unconfirmed, task_success null, and replay denied. This is a separate Xvfb attempt but adds no new discriminator: commit 422f7ea6 changed pending-response test handling, not the cleanup request or diagnostic propagation. The `invalid_fields` field is still absent from the public result because the owner adapter fix is in a later commit. Preserve this raw outcome; do not count it as a release result or an independent discovery.

The sibling `x11-integration` job completed successfully: 77 Xvfb integration tests and 5 server-stop/recovery tests passed after the tests began separating bounded cancel responses from terminal receipts. Its distinct standard-caller raw results are preserved under [`standard-caller/`](standard-caller/README.md). This success does not change the failure of the isolated prestarted-supervisor job.

## Scope

This failed real-Xvfb composition attempt does not establish release, task effect, recovery, reliability, WSLc portability, MAP01, or matched efficiency.
