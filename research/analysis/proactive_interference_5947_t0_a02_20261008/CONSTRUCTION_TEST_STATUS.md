# A02 construction-test status — attempt 1

This is an append-only construction record. No formal candidate/auditor execution or freeze occurred.

The test-first contract exposed multiple design defects before formal allocation:

1. Current cue byte offset was mistakenly computed after the cue and was identical for every condition/arm; the position control offset was incorrectly derived from prefixes whose markers were only in the history slot.
2. Fixed padding was appended after variable history. That held total bytes but did not keep common suffix bytes exact; history slots could exceed the pad at depth 8.
3. The raw JSON interface cannot encode Python bytes directly, while the test mutation helper is undefined in the test module.
4. Baseline-change records need full baseline source/value equality checked from serialized identity, not merely source-id cross-check.

This record makes no claims about candidate/auditor PASS. Next construction patch will encode all byte fields as UTF-8/base64-decodable hex text in JSON, use a fixed exact prefix and suffix, isolate history in a fixed-capacity slot, put a unique current-cue marker in the shared prefix, define mutations in the test module, and require the independent auditor to verify exact baseline object/source bytes, complete group row identities, expected row IDs/arms/depths, and the separate position-control-only offset change. Rerun construction tests only; freeze remains deferred until all controls pass.
