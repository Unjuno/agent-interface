# #59 V39 current-main source identity audit A02

**Disposition: `HOLD_SOURCE_IDENTITY_STALE` for reusing the r139 controller freeze.** This is a read-only static source review, not a live behavior result. The audit ran once against main `b4046798ed8902745a36e8fda091204233bb06d3` and exited 0.

The current-main top-level V39 controller SHA-256 is `51ceed1ee329da2c64cf26300acddcf3e57b03ad8b193716709dcc0a95143607`, while r139 and its hash-bound triage cite `4548ca30b5a962946c7f81a58784a5b8e672a10635f4737c36b38f596b2c27ca`. The historical `c1074...` tree does contain the cited controller hash. The V15 session remains byte-identical at `661b3ac311f72517670a8fe37bc2901e9479963af9cdb0a219ed83ea48601724`. Thus the current direction's controller source reference is stale relative to the frozen current-main tree; this difference alone does not prove a behavioral regression.

Static AST inspection of the current controller and its actual imported monitor found that the cover monitor reads a typed health signal and optionally a paired ammo signal. It checks frame hashes for observation coherence, not scene meaning; no full-scene enemy/threat classifier appears in that monitor path. The controller contains pending-model monitor delivery, planner interruption on invalidation, and terminal checks for verified release with empty keys/buttons. These are source facts only and do not show that any guard fired, how quickly it would react, or that physical input was released in a live game.

A01 is retained as `HOLD_AUDIT_INPUT`: its one invocation stopped before producing a source finding because its audit harness expected the imported monitor class to be defined inside the controller module. A02 parses the actual helper source and does not rerun A01. The independent #8256 retained-data audit and #8257 cleanup-receipt correction remain separate and unchanged.

The fresh threat-exposure experiment remains the next empirical gate. Current main says the private game lane is unassigned; no controller, session, game, GUI, model, input, or container code was executed here. No code repair is justified by this static review.

## Custody

- `FREEZE.json` binds the current-main commit and all source inputs.
- `results/source_audit.json` is the retained structured output; `results/source_audit.stdout` preserves the exact first stdout.
- `RUN.json` records the one invocation, exit code and raw hashes.
- The A01 first failure remains in `../v39_current_main_source_identity_audit_a01_20261009/FORMAL_FAILURE.md` and was not retried.
