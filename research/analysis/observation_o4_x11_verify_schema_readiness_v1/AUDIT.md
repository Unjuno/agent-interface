# Independent audit

Source identity matches the pinned main blobs in Issue #1843. The retained JSON contains 3 FRESH and 3 STALE arms. FRESH arms all have caller_reason=verified_effect and positive exact_effect_delta; STALE arms have caller_reason=stale and null effect delta. None of the six arm objects contains any of: obs, intent, verdict, input_authority, semantic_authority.

Therefore strict #1650 admission is 0/6 without inventing lineage. The naive comparator suppresses 3 FRESH rows. Corruption controls are fail-closed by construction: fabricated IDs/authority flags are not present in retained bytes and stale relabeling is not accepted as a current receipt.

Disposition independently recomputed: HOLD_O4_X11_SCHEMA_INSUFFICIENT.
