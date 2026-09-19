# Optional local supervisor v1

This is a deliberately small, optional local learned component for the high-frequency refinement loop. It predicts only `CONTINUE` or `YIELD` from typed state features. It cannot emit coordinates, pointer/keyboard operations, leases, target references, or task success. The caller must still perform fresh observation, ordinary admission, effect verification and release.

The rich model remains the semantic planner. This module is a local GPU-capable experiment and is not a mandatory intermediary. When confidence is below the caller threshold, the result is `YIELD`.
