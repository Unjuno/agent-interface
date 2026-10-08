# Scope

This is a bounded, pure validator for advisory planner handoff context. It rejects
identity mismatch, expiry, contradiction, missing uncertainty, and any implicit
authority transfer or replay permission. Accepted capsules always require fresh
authority acquisition.

It does not transfer authority, replay actions, call a planner, inspect a GUI,
measure recovery, or establish task correctness.
