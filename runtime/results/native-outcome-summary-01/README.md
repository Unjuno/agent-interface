# Native outcome summary: retained-result check

The preceding Calc final-action run (#3195) recorded saved-file success together
with needs_review/BadWindow feedback. A direct-field summary now exposes both
before the complete receipt. It does not resolve the residual dialog pixels,
recapture the screen, grant authority, or change scoring and cleanup.

`result.json` records a read-only presentation of the original local reply-2.json
from native-calc-final-action-01. The report and image hashes were unchanged;
compact expansion matched the full receipt and both returned the same image.
No new GUI run, model helper, or sensor was used. `check.py` reproduces this check
from the original local run; it requires that run and its recorded image paths.
The original evidence is retained separately in PR #3195, not duplicated here.

Validation: 32 tests passed across test_agent_review, test_receipt_references and
test_native_exchange_v1. The first test attempt incorrectly used the non-native
receipt expander and failed one test; correcting the test to use the native
expander produced the passing run. No production change was needed for that fix.
Tests include malformed/missing values, false evaluation despite finished,
history exclusion, damaged images, full/compact agreement and source immutability.

Scope: faithful presentation only. Metadata grows by 165 UTF-8 JSON bytes with
compact separators on this full receipt excluding inline image data. This is not
a token saving, latency improvement, model-accuracy result or visual-completion
claim. Existing image_status reports image validation, not rendering freshness.
