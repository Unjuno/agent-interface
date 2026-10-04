# Scorer feedback attribution construction A03

## H / T / D / C / U

**H:** Timestamp equality alone cannot establish whether a scorer sample occurred before admission or after a release/XSync. More broadly, admission through release/XSync are outer bounds on a possible hold window, not proof of continuous key-down. These data can name at most a possible intent envelope, never confirmed held-input coverage.

**T:** Exercise the A01 review counterexample (`samples=[100,200]`, verified interval `[90,200]`) and the other endpoint tie (`[100,210]`), plus strict coverage, partial coverage, multiple intents, release uncertainty, gaps, duplicate intervals, and a sample identity mismatch. Compare A01 and this successor on the endpoint cases.

**D:** Both endpoint ties must be `UNRESOLVED`. Strictly spanning verified bounds may report `SINGLE_POSSIBLE_INTENT_ENVELOPE`, with only a possible intent token and no unique `intent_token`; all other conservative dispositions must remain unchanged. Causal attribution remains unestablished.

**C:** A source sequence that authentically orders both sample and key lifecycle events could resolve a tie; this construction has no such order and must not invent one. Conservative timestamp bounds may reduce useful labels.

**U:** Synthetic construction only. No live session, game, model, GUI, input, or allocation was used. This does not establish scorer accuracy, task effect, latency, causality, or MAP01 completion.

## Outcome

The A01 helper labels the review's `[90,200]` tied-release case `TEMPORALLY_UNIQUE`. A03 leaves both endpoint ties unresolved and downgrades even strictly spanning bounds to `SINGLE_POSSIBLE_INTENT_ENVELOPE`; it never names a unique intent or claims confirmed hold coverage. This addresses both endpoint ordering and the admission/release-envelope limitation in the PR discussion. The lifecycle input still lacks post-press acknowledgement and pre-release-request bounds, so a guaranteed-held interval cannot be established. Thirteen local unit tests and the independent saved-result audit passed. A separate successor #7544 handles same-session identity; this package does not duplicate that guard. Historical A01 files and the A02 retained-stream application are untouched.

Run from this directory with `python -m unittest discover -s . -v`. See `RESULT.json`, `AUDIT.json`, and `FILES.sha256` for the captured run and source identities.
