# P11 sanitized publication derivative

This directory is a privacy-safe summary of the local P11 packet. `CONDITIONS.json` and `PREREGISTRATION.md` are copied byte-for-byte from the original packet after a local profile-path scan found no matches. `RESULT.md` and `AUDIT-SUMMARY.json` retain only bounded aggregate facts and disclosed limitations.

The source packet remains local-only because its immutable provider/MCP `.bin` records contain a local Windows profile path. Its 522-entry manifest was checked in place, all 10 preregistered runtime source hashes matched current main, all six runner hashes matched, and the recorded local audit classifies all six cells at 15/15. The original packet, raw records, and audit output were not copied, scrubbed, rewritten, or rerun.

This derivative allows readers to inspect the preregistration, conditions, scoped result and limits. It does not let readers replay the raw audit independently. Treat it as a sanitized result summary, not a substitute for public raw custody.
