# Issue #3690 — Docker Desktop host integration

This is a fresh, bounded engine-specific validation of the exact final #3683 hardened auditor source. Existing OrbStack container results remain unchanged and are not represented as Docker Desktop evidence.

Two fresh containers are invoked exactly once each: (1) the exact five-test suite, then (2) the raw-only CLI against the frozen predecessor trace. The second output is byte-compared with the already retained baseline. No XRes/X11 formal allocation, GUI, input, game, or model activity is involved.

Protocol and identities are in `PREREG.md` and `SOURCE_MANIFEST.json`. Run `run_formal.ps1` once; it refuses an existing output directory or any source, engine, platform, or image mismatch.
