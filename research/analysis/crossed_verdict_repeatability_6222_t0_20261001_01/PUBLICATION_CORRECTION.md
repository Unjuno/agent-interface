# Publication correction: candidate transport truncation

The formal local candidate and independent audit completed once under allocation `CROSS-VERDICT-REPEATABILITY-6222-T0-HOST-20261002-01`. During the first GitHub publication, the local command-output transfer was capped and only a prefix of `candidate.json` was committed at the evidence path. A remote byte-count/readback comparison detected this before PR creation. The formal local file remains unchanged (93,557 bytes; SHA256 `ce85e4970fdc9467acc918f10b3c23f8b175283878fa2d505eeadaa6af839696`); the independently produced audit binds that exact SHA256 and reconstructed all 288 rows. The first short transport commit remains in branch history as a publication error, not an alternate scientific result.

The evidence path is being corrected additively in a follow-up commit using the exact local file bytes. The replacement must resolve to Git blob SHA `b81095a1bdca2887ef7a3ab8c59437ca61db5fb8` and size 93,557 bytes before the PR can be considered complete. No candidate, auditor, or experiment was rerun or altered. Preserve this note and the earlier commit as provenance.

