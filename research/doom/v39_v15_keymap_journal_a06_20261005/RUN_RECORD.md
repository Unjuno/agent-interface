# A06 run record

- Preregistration: Issue #59 comment 5986764896, posted before execution.
- Frozen base: main commit 5a290af598e4ef365ac5dfe66dca2c3c9916a20a. Candidate SHA-256: e2483233bb48b995058fd459d016574d1f7e7ab6c80db540c7f03637ba1623c0.
- Candidate: one invocation at 2026-10-05 01:55:59 UTC, Python 3.11.9, Windows, exit 1. No retry or repair.
- Auditor: one independent raw-only invocation at 2026-10-05 01:57:11 UTC, exit 0. Its output records all 13 checks.
- The normal case completed and was journaled: both keycodes were up and both rows sampled as verified.
- The one-shot injected drop case was journaled as a failure with its full trace and partial release rows. The post-batch sampler ran after both explicit UPs, observed SPACE (keycode 65) still down and F8 (74) up, and downgraded only SPACE. The terminal v12 cleanup then failed closed with `owner release not verified: [65]`. Because explicit UP bookkeeping had already removed SPACE, cleanup did not issue another KeyRelease.
- The sampler-unavailable case was not reached. Overall disposition: `STOP_OWNER_CLEANUP_CANNOT_RECOVER`; the preregistered full-pass criteria were not met.
- This synthetic result does not claim real X11 or physical keyboard truth, application consumption, task success, real V39/V15 startup, useful feedback, recovery efficacy, latency, or gameplay.
