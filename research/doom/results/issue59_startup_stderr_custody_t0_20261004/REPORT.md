# Issue #59 startup-stderr custody diagnostic T0

**Disposition: `PASS_METHOD_SCOPED`.** One OrbStack candidate invocation and one independent raw-only audit completed four deterministic subprocess cases. When a child exited before `ready`, its original exit outcome remained primary and stderr was retained with a byte count, full-stream SHA-256, bounded prefix/tail and truncation flag. A 262,144-byte stderr stream completed without deadlock; a no-ready child timed out, received SIGTERM and closed with its diagnostic preserved; the success control retained the exact ready event. All four raw corruption controls were rejected.

## Evidence

- Preregistered scope and gates: [`src/PLAN.md`](src/PLAN.md).
- Frozen input/source hashes and pinned runtime commands: [`src/freeze.json`](src/freeze.json), SHA-256 `8cb8db1fa7f7c8c7b50e85d3d4c78a5c319959313f733063bb28306a22e76004`.
- Candidate subprocess records: [`raw/candidate.json`](raw/candidate.json), SHA-256 `8be2929ed4752b2b98aaae2ccb0cdde94e11c4653c464041fcff5d230c3dbe6b`.
- Independent audit: [`raw/audit.json`](raw/audit.json), SHA-256 `343612b8d514edd68c3956f551cf3a2a4b1d9311e19b8fcecb9b2d5105525812`.
- Commands, exits, stdout and no-retry receipt: [`raw/execution_receipts.json`](raw/execution_receipts.json).

Elapsed times were 30.244 ms (short exit), 31.086 ms (large stream), 623.396 ms (600 ms timeout plus cleanup), and 86.651 ms (ready success); all were below the 2 s gate. The large-stream collector retained 8,192 bytes total while hashing/counting all 262,144 bytes. The kernel pipe capacity was not measured, so this is a 256 KiB streaming stress result, not a measured claim about a particular pipe-capacity threshold. Docker resource limits were requested; effective memory enforcement was not independently established.

OrbStack's full image-catalog listing failed during preflight on a missing containerd blob. The exact already-pinned Node digest still inspected and ran successfully; no image pull, daemon restart, or repeated catalog attempt was made. The infrastructure anomaly is retained in the execution receipt and is not classified as a candidate failure.

## Interpretation boundary

This does **not** identify the cause of the retained `controller-visual-01` `STOP_SESSION_BEFORE_READY`, modify its evidence, qualify current-main v39/V16 controller cleanup, or establish a live game/model result. A later actual visual-controller run is separately retained in PR #7570 and still ended HOLD for useful recovery. This T0 only demonstrates a diagnostic-capture method for synthetic child processes; Issue #59's current live threat/recovery gate remains open and its shared game lane remains unassigned. Formal invocations were not retried.

**Current-main follow-up (after this T0 freeze):** PRs #7571/#7572 retain a four-turn visual recovery window and a later post-refusal re-admission episode. The latter demonstrates a distinct fresh accepted input after invalidation, but still has zero independent useful-effect events and remains `HOLD` for useful recovery; interrupted-turn token-cost attribution is also unresolved. The next #59 experiment should target a genuinely independent same-episode useful-effect/recovery decision or a matched strong-simple reference—not another seed/iteration expansion. This startup diagnostic is ancillary and does not satisfy that next gate.
