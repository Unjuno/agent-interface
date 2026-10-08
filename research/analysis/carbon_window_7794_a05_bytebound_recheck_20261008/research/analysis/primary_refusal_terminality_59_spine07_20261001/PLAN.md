# #59 spine-07 caller malformed-envelope boundary

## H / T / D / C / U

**H.** The frozen spine-07 primary caller converts a malformed host reply into a latched STOP before the primary can catch the parse exception and issue another effectful input.

**T.** Against current PR #5639 head `04c9e041d3c5e7c9d06e21a94f8fd0b2b483102d`, execute one Node process importing the exact `runtime/results/post-release-spine-07/construction/primary-policy.mjs` Git blob `b2f27b6cda362db24e906090f33c4813d60f2867`. A mock host returns an invalid envelope on the first `interface_dispatch`; the primary-like caller catches the thrown parser error, then attempts one more dispatch. The mock's second response is completed-shaped with a neutral release. Retain exact process output. No GUI, MCP service, model, X11, input, game, Docker, network, retry, or external side effect.

**D.** PASS only if the malformed envelope latches STOP and prevents the second host dispatch. A second effectful call reaching the mock is `FAIL_UNCERTAIN_DELIVERY_REPLAY`. Provenance or raw-output mismatch is STOP.

**C.** One deterministic mock sequence; it tests caller terminality, not transport truth or application semantics. A malformed envelope may stand for many distinct malformed fields.

**U.** No live host/MCP, physical input, task effect, threat exposure, release latency, MAP01 efficacy, efficiency, or product claim. This is a focused construction regression on the current PR candidate, not a new live allocation and not a rerun of the previous source blob from PR #5639 spine-05.

## Frozen identities

- Current GitHub main at intake: `d3bf9aa2b49a1f688a9c709aa876db23aaf3f15d`.
- Current GitHub main at evidence packaging: `4303c2dea4b95e2f8f0eb7d2fbd895946ca62872`.
- Candidate PR: #5639, branch `integration/post-release-feedback-20261001`, head `04c9e041d3c5e7c9d06e21a94f8fd0b2b483102d`.
- Candidate file Git blob SHA: `b2f27b6cda362db24e906090f33c4813d60f2867`.
- Current delivery main: `e0da9cd0862f4b325f5f245fe6f70a5a12198106`. Current PR #5639 head is `83367dc9299237733112d6eef4b0e6ce18781ef8`; a post-run readback confirms the tested file remains the same Git blob SHA above.
- Run count: one Node process; two caller attempts total (first malformed, second replay probe). No rerun.

The evidence path and analysis-index update are additive; no predecessor result or PR branch was changed.
