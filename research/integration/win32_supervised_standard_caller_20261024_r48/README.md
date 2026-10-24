# R48 independent paired native-Windows replication

Attempt `win32-supervised-recovery-fresh-generation-task-20261024-r48-0169b23ca60f4a859395051020e16318` is a single fresh native-Windows fixture sequence on the user-authorized PC. It repeats the frozen bounded cancel/release gate once, then runs one separately identified fresh-generation fixture task with an independent server oracle only if phase 1 passes. See `conditions.json` for exact protocol, limits, source hashes, IDs, stop rules, and exclusions. No WSLc or Docker operation is part of this attempt.

Public packet manifests: `SHA256SUMS` records the original pre-redaction bytes preserved in the local private evidence store; `SHA256SUMS_PUBLIC_R01` verifies the sanitized public derivative. See `PUBLICATION_CUSTODY.json` for the additive custody and redaction counts.
