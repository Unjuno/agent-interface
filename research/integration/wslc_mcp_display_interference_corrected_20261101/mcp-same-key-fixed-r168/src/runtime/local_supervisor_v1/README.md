# Optional local supervisor v1

This is a deliberately small, optional local learned component for the high-frequency refinement loop. It predicts only `CONTINUE` or `YIELD` from typed state features. It cannot emit coordinates, pointer/keyboard operations, leases, target references, or task success. The caller must still perform fresh observation, ordinary admission, effect verification and release.

The rich model remains the semantic planner. This module is a local GPU-capable experiment and is not a mandatory intermediary. When confidence is below the caller threshold, the result is `YIELD`.

## Distribution and speed budget

The current source/result bundle is 5,538 bytes and is intentionally GitHub-native: no Git LFS, model server, download step, or external workflow is required. Keep this component below 64 KiB for source plus metadata. If learned weights later exceed that budget, retain the fast rule-based/YIELD path and require a separate measured justification before introducing a larger artifact.
