# Pre-formal source freeze

Issue #4116, allocation `wal-multi-reader-reclamation-4086-20260922-01`.

This directory was committed before formal batch 0. The exact frozen source/environment/auditor bytes are the XZ archive reconstructed by concatenating `preformal-source-00.b64` and `preformal-source-01.b64`, Base64-decoding once, and verifying SHA-256 `d41254654872439641aa20132b52da795277408da370cc8978381032baab882c`.

Construction history is inside that capsule. Construction-00 completed the fixture but exposed a pre-freeze auditor error: it incorrectly expected a released reader's later DB sample to remain pinned. The audit-only assumption was corrected; construction-01 then passed 6/6. No scientific schedule or decision gate changed.

Formal schedule: two immutable batches of six cases, 12 cases total, 768 writer transitions. No rerun/replacement/exclusion/post-freeze source change.
