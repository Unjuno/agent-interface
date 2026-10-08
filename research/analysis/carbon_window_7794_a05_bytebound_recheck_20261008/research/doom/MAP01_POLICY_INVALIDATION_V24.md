# MAP01 v24 one-way policy invalidation

Controller v24 revisits the earlier changed-pixel candidate under a narrower
authority contract.  A configured exact-frame ROI may only invalidate an
already admitted cover policy.  A changed or unknown result cancels that cover,
waits for its terminal release, and discards the model action computed from the
invalidated source.  The following iteration starts from a fresh observation
with coast; it cannot reuse the discarded action's `next_cover`.

The guard does not classify what changed, prove damage, prove task success, or
authorize replacement input.  Binding mismatch, malformed frames,
nonadvancing sequence, invalid time, and source expiry all fail closed to a new
decision.  The model call is allowed to finish so its complete output and usage
remain auditable, but none of its commands or cover policy are admitted after
invalidation.

The first configured candidate is the tight health-number ROI
`[440,585,535,635]`, RGB threshold 32, minimum 100 changed pixels.  This is a
MAP01-specific sensor configuration over a generic one-way guard, not a general
visual semantic parser.  Health pickups and damage can both invalidate it; that
ambiguity is acceptable here because both outcomes only remove authority.

`test_map01_policy_invalidation_v24.py` replays all 65 retained lossless ROI
samples from v23 cover 5.  The first invalidation occurs at sequence 250,
1,570.425128 ms after the retained source time, with 400 changed pixels.  It
also verifies that a discarded action cannot supply the next cover.  The
generic guard boundary suite separately checks the exact changed-pixel
threshold and five fail-closed unknown conditions.

This is replay and contract evidence.  It does not show that cancellation
improves survival, latency, progress, or MAP01 completion.  Those questions
require a separately frozen live allocation with retained admission, release,
discard, HUD, model, and outcome evidence.
