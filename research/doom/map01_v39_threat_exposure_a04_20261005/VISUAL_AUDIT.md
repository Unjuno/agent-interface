# Visual evidence review

The audit script validates image hashes and file presence; it does not classify enemies. The following frames were visually inspected from the frozen raw archive:

- `runtime/205.png` (SHA-256 `748a183d770cebb7d12f8ffd3186f07ac613e4cd23935468ffbed8c0dd843269`) was captured after `cover-4` was accepted. The enemy is close and centered; typed HUD is health 30, ammo 43.
- `runtime/216.png` (SHA-256 `a9b4a14e719fd353272806fa74f8ee20882c3b33a82cf48a5ccc638ac50645f4`) is the observation that caused the invalidation. The enemy remains visible close at the right; typed HUD is health 30, ammo 42.
- Their capture timestamps are 1.441 s apart. The authored `retreat_fire` cover was active for this interval. The discrete one-round decrease was first treated as `SOFT_CHANGED` and preserved the policy. The later cancellation reason was `health:source_expired` at source age 1,605.6 ms, with health unchanged at 30.
- `decision-4/temporal-sheet.png` (SHA-256 `40f12a74ebee07b8d43684c9a651a27de73f303b7a3290cf4e7bbb98a66c828a`) and `decision-0/temporal-sheet.png` (SHA-256 `6718881b430ad1de2fab16e9651d038d3e0f92244acd1742bc1eec3607abf3b0`) show the source images used for the corresponding model calls.

This establishes a visible threat and changing typed ammo during an authored-cover/pending-turn interval. It does not establish a causal health-saving effect. The stop was for expired source evidence, not a semantic health change. The cancellation was followed by an empty-key owner state, then a 12.7 s fresh model wait in which health fell from 30 to 4.
