# Scorer feedback attribution construction A03

## H / T / D / C / U

**H:** Timestamp equality alone cannot establish whether a scorer sample occurred before admission or after a release/XSync. A temporal association is unique only when one verified intent strictly brackets both scorer sample timestamps and no other intent could overlap.

**T:** Exercise the A01 review counterexample (`samples=[100,200]`, verified interval `[90,200]`) and the other endpoint tie (`[100,210]`), plus strict coverage, partial coverage, multiple intents, release uncertainty, gaps, duplicate intervals, and a sample identity mismatch. Compare A01 and this successor on the endpoint cases.

**D:** Both endpoint ties must be `UNRESOLVED`, with no intent token and causal attribution left unestablished. Strict coverage may remain `TEMPORALLY_UNIQUE`; all other existing conservative dispositions must remain unchanged.

**C:** A source sequence that authentically orders both sample and key lifecycle events could resolve a tie; this construction has no such order and must not invent one. Conservative timestamp bounds may reduce useful labels.

**U:** Synthetic construction only. No live session, game, model, GUI, input, or allocation was used. This does not establish scorer accuracy, task effect, latency, causality, or MAP01 completion.

## Outcome

The A01 helper labels the review's `[90,200]` tied-release case `TEMPORALLY_UNIQUE`. A03 changes the rule to require strict inequalities at both boundaries; both `[100,210]` and `[90,200]` now remain unresolved. Twelve local unit tests passed. The historical A01 files and A02 retained-stream application are untouched.

Run from this directory with `python -m unittest discover -s . -v`. See `RESULT.json`, `AUDIT.json`, and `FILES.sha256` for the captured run and source identities.
