# First posthoc descriptor INVALID, preserved without replacement

DESCRIPTIVE.json initially selected cell IDs with startsWith('p'), accidentally
including persistent_* controls. It wrongly pooled49vs49 events,7pairs and
counted5qualifying differences. These are NOT the frozen primary computation.
The original file is retained; do not use it. Source/official saved audit use
kind=='pulse', correctly48vs48events/6pairs/4qualifying differences/678690.5ns
pooled reduction and HOLD_NOT_REPRODUCED. No acquisition/auditmain was replayed.

DESCRIPTIVE_V2.json is a new corrected posthoc result: selected using the exact
published FREEZE.cases map and guarded12pulse cells/48events each/6pair identity.
Both versions retain the original raw data and frozen primary result unchanged.
QUERY.md's source extraction is valid; its later written pooling description
requires case.kind=='pulse', NEVER prefix-only selection. Descriptor code
uses median sorted middle (mean two middle for even n), and verifies counts.
