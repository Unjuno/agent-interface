# A14 per-key release raw re-audit A15

**Result: `PASS_RAW_REAUDIT` for a saved historical artifact.** This is a read-only re-analysis of selected A14 files, not a rerun of its live allocation. The original A14 freeze deviation remains intact and invalidates its preregistered efficacy claim.

The WSLc replay verified 10 identity-bound per-key XTest `KeyRelease` records: each key had a matching admission and held-step record, exactly one key-up attempt, successful XSync, server keymap down-before/up-after, no recorded owner-cleanup interference, and an ordered per-key batch position. For the two health-source-expiry cancellations (`cover-2`, `cover-5`), 2 and 3 step-level key-ups respectively preceded `input_released` and the terminal event. Their retained terminal receipts pass PR #8835's exact strict known-empty predicate; mutation controls confirm omitted `keys_unknown` or `key_state_errors` are rejected.

The evidence is explicitly X-server-level. Every per-key receipt sets `physical_verification_authoritative=false`; this cannot establish the physical keyboard state outside X11. The cancelled planner turns were triggered by expired health observations above their hard floor, not a health/ammo hard-boundary crossing, and the run did not complete MAP01. No live allocation was started or repeated.

The raw files are copied byte-for-byte from A14 commit `2d16f5f`; `inputs/raw-sha256sums.txt` is the original checksum manifest and the test recomputes checksums for all copied raw inputs. The exact PR #8835 predicate snapshot and its Git blob identity are retained. WSLc 3.0.1.0 ran both normal and optimized CPython 3.14.8 modes with network disabled, read-only sources, one requested CPU, and 512 MiB requested memory. Host swap limits are unsupported, so no swap enforcement is claimed. The post-run container inventory is empty.

See `FREEZE.json`, `RUN.json`, `SOURCE_MANIFEST.json`, `AUDIT.json`, raw logs, and `REPRODUCE.md`. This re-audit strengthens the provenance of server-side per-key release observations but does not remove A14's protocol deviation or establish live control efficacy.
