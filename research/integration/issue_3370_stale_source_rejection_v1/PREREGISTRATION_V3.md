# Preregistration addendum — sealed current-main allocation

The previously observed `stale_source_v2` behavior and its passing audit are
retained for engineering context, but excluded from the formal pass count: a
final comparison found that `SOURCE_FREEZE_V2.json` did not hash the exact
client/auditor contents used by that allocation. No files in that evidence tree
are rewritten. The first receipt-shape STOP and the sequence-zero development
probe are likewise preserved and excluded.

This sealed trial freezes current main `21425ed43b55d7eeb1b608d2e127c9fab7f6acc8`,
all target runner/dependency hashes, the exact client, independent auditor,
preregistration and manifest script in `SOURCE_FREEZE_V3.json`. It uses a new
OrbStack owner and evidence path `evidence/stale_source_v3/`, same pinned image,
same seed 991123, and the exact one-shot stale action followed only by the
pre-registered read-only observation and no-input finish. Every file hash must
match before launch; any mismatch is STOP-before-allocation. No retry or
corrected action is allowed inside the fresh owner.
